from PyQt5.QtCore         import Qt
from PyQt5.QtGui          import QIcon, QMovie
from PyQt5.QtWidgets      import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPlainTextEdit, QPushButton, QCheckBox, QComboBox, QMessageBox, QFileDialog
from electroncash.plugins import BasePlugin, hook
from electroncash         import bitcoin
import electroncash, subprocess, threading, zipfile, shutil, gc, random, time, platform

def push_script(script):    #Bugfix for Message size 255B.
        if len(script)>>1!=255: return bitcoin.push_script(script)
        else:                   return '4cff'+script
class Plugin(BasePlugin):
    def __init__(self, parent, config, name):
        BasePlugin.__init__(self, parent, config, name)
        self.windows, self.tabs, self.UIs = {}, {}, {}  #Initialize plugin wallet "dictionaries".
        
        Dir=self.parent.get_external_plugin_dir()+'/VanityTXID/'
        self.WebP=Dir+'bin/Icon.webp'    #QMovie only supports GIF & WebP. GIF appears ugly.
        self.WebPButtons=[Dir+'bin/IconTXID.webp', Dir+'bin/IconP2SH.webp', Dir+'bin/IconHash.webp']
        if shutil.os.path.exists(Dir): Extract=False   #Only ever extract zip (i.e. install) once.
        else:
            Extract=True
            Zip=zipfile.ZipFile(Dir[:-1]+'-Plugin.zip') #shutil._unpack_zipfile is an alternative function, but it'd extract everything.
            Zip.extract('bin/Icon.webp',Dir), Zip.extract('bin/LICENSE.txt',Dir)
            {Zip.extract(WebP[len(Dir):],Dir) for WebP in self.WebPButtons}
        if 'Windows' in platform.system():
            if '64' in platform.machine():  binDir='bin/Windows/'
            else:                           binDir='bin/Windows-x86/'
            self.exe = [Dir+binDir+'VanityTXID-Plugin.exe', Dir+binDir+'VanityP2SH-Plugin.exe', Dir+binDir+'VanityHash-Plugin.exe']   #Keeping C++ code separate seems wiser than combining it into one exe.
            if Extract: {Zip.extract(Item,Dir) for Item in Zip.namelist() if Item.startswith(binDir)}
        else:
            binDir='bin/'+platform.system()+'/'
            self.exe = [Dir+binDir+'VanityTXID-Plugin', Dir+binDir+'VanityP2SH-Plugin', Dir+binDir+'VanityHash-Plugin']
            if Extract:
                {Zip.extract(exe[len(Dir):],Dir) for exe in self.exe}
                subprocess.Popen(['chmod', '+x', self.exe[0], self.exe[1], self.exe[2]])
        if Extract: Zip.close()
        self.Icon=QIcon()   #QMovie waits for init_qt. self.Icon isn't necessary, but I suspect it's more efficient than calling QIcon for all wallets.
    def on_close(self):
        """BasePlugin callback called when the wallet is disabled among other things."""
        del self.Movie  #Movies are special and must be deleted.
        {self.close_wallet(window.wallet) for window in self.windows.values()}
        shutil.rmtree(self.parent.get_external_plugin_dir()+'/VanityTXID')
    @hook
    def init_qt(self, qt_gui):
        """Hook called when a plugin is loaded (or enabled)."""
        if self.UIs: return # We get this multiple times.  Only handle it once, if unhandled.
        self.Movie=QMovie(self.WebP)    
        self.Movie.frameChanged.connect(self.setTabIcon), self.Movie.start()
        {self.load_wallet(window.wallet, window) for window in qt_gui.windows}  # These are per-wallet windows.
    @hook
    def load_wallet(self, wallet, window):
        """Hook called when a wallet is loaded and a window opened for it."""
        wallet_name = wallet.basename()
        self.windows[wallet_name] = window
        l = UI(window, self)
        tab = window.create_list_tab(l)
        self.tabs[wallet_name],self.UIs[wallet_name] = tab,l
        window.tabs.addTab(tab,self.Icon, 'VanityTXID') #Add Icon instantly in case WebP frame rate is slow.
        window.toggle_tab(tab)
    @hook
    def close_wallet(self, wallet):
        wallet_name = wallet.basename()
        {process.terminate() for process in self.UIs[wallet_name].process if process}
        {Thread.join() for Thread in self.UIs[wallet_name].Thread if Thread}    #Wait for termination to pause movies.
        del self.UIs[wallet_name].Movies
        del self.UIs[wallet_name]   #Delete UI now to stop Movie's tab connection, before tab removed.
        window = self.windows[wallet_name]
        window.tabs.removeTab(window.tabs.indexOf(self.tabs[wallet_name]))
        del self.tabs[wallet_name]
    def setTabIcon(self):
        self.Icon.addPixmap(self.Movie.currentPixmap())
        for wallet_name in self.UIs.keys():
            Tabs=self.windows[wallet_name].tabs
            Tabs.setTabIcon(Tabs.indexOf(self.tabs[wallet_name]),self.Icon) #It's probably more elegant to keep track of each tab index using a pyqt5 signal connection, instead of constantly asking for it. I'm not sure how.
class UI(QDialog):
    MaxMessage=520 #Other languages like Chinese require a few bytes per character.
    ButtonText=['Sign TX &&/or Generate TXID', 'Generate Vanity P2SH Address', 'Generate Vanity SHA256 Checksum (select files or drag && drop)']
    BCH32='qpzry9x8gf2tvdw0s3jn54khce6mua7l'
    
    def __init__(self, window, plugin):
        QDialog.__init__(self, window)
        self.window, self.plugin = window, plugin
        self.UIdict={}   #Store all VanityTXID addresses in a dictionary. This dict is used to ask wallet for private key/s when needed. Has form {P2SH: Script,P2PKH}. Updated using Search button etc.
        self.process=[None, None, None]   #[TXID, P2SH, Hash]
        self.Thread=[None, None, None]   #Useful for joins, due to playing movies.
  
        self.setAcceptDrops(True)     #Drag & Drop.
        self.Paths=None  #Used by drag & drop.

        self.HiddenBoxes=[QPlainTextEdit() for n in (0,1,2)]   #Hidden textboxes allow primary Qt thread to show_transaction & show_message etc. Only primary thread is allowed to do this.
        {self.HiddenBoxes[n].textChanged.connect((self.show_transaction, self.ShowMessageBox, self.show_message)[n]) for n in [0,1,2]}

        self.Buttons=[QPushButton(Text) for Text in self.ButtonText] #Animated buttons.
        {self.Buttons[n].clicked.connect((self.clickedTXID, self.clickedP2SH, self.clickedHash)[n]) for n in (0,1,2)}
        self.Buttons[2].setToolTip("Without a valid target, an 8 Byte tail is added to the files.\nLarge files may cause power failure to CPU, if required memory for all threads exceeds RAM.\n.iso & often .zip require an internal target, whereas .exe, .webp, etc can have a tail appended.\nNo folders, only files.\nDrag & drop may not work in Linux.")

        Title=QLabel('VanityTXID v1.6.2 (+VanityP2SH+VanityHash)')
        Title.setStyleSheet('font-weight: bold'), Title.setAlignment(Qt.AlignCenter)
        
        Example = QPushButton('Example')
        Example.clicked.connect(self.Example)
        
        HBoxTitle=QHBoxLayout()
        HBoxTitle.addWidget(Title,1), HBoxTitle.addWidget(Example,.1)

        self.HashPattern=QLineEdit()
        self.HashPattern.setMaxLength(32)   #8B nonce.
        self.HashDifficulty=QLabel()
        self.HashDifficulty.setToolTip('Difficulty estimate, in MH.\nHashing difficulty increases with file size.')
        self.HashPattern.textChanged.connect(self.HashDifficultyChanged)
        self.HashPattern.setText('000')
        
        self.NonceTargetBox=QLineEdit('<#Nonce>')
        self.NonceTargetBox.setToolTip("Optional.\nTarget for nonce placement.\nThe first instance of this string will be replaced by a nonce.\nDon't use a filename.\nv1.6.1 used 'VanityHashNonceF'")
        self.NonceTargetBox.setAlignment(Qt.AlignRight)
        
        HBoxHash=QHBoxLayout()
        HBoxHash.addWidget(QLabel('(hex) SHA256 Checksum Starting Pattern: '))
        {HBoxHash.addWidget(Widget) for Widget in (self.HashPattern, self.HashDifficulty, self.NonceTargetBox)}
       
        AddressesLabel=QLabel('VanityTXID Addresses: ')
        ConverterLabel=QLabel('Address to Convert: ')
        AddrPatternLabel=QLabel('CashAddr Starting Pattern: ')
        
        self.BoxReadOnly=QCheckBox('Read-only')
        self.BoxReadOnly.toggled.connect(self.setReadOnly)
        
        ScriptLabel=QLabel('(hex) Script: ')
        HBoxScript=QHBoxLayout()
        {HBoxScript.addWidget(Widget) for Widget in (self.BoxReadOnly, ScriptLabel)}
        
        VBoxAddressesLabels=QVBoxLayout()
        {VBoxAddressesLabels.addWidget(Label) for Label in (AddressesLabel, ConverterLabel, AddrPatternLabel)}
        VBoxAddressesLabels.addLayout(HBoxScript)
        
        self.AddressLine=QLineEdit()
        self.AddressLine.setReadOnly(True)
        self.SearchContacts()
        self.AddressLine.setToolTip('Only these addresses can definitely be signed for. Not necessarily all contacts & contracts.')
        SearchButton=QPushButton('Search Contacts')
        SearchButton.clicked.connect(self.SearchContacts)
        HBoxAddresses=QHBoxLayout()
        {HBoxAddresses.addWidget(Widget) for Widget in (self.AddressLine, SearchButton)}

        self.Converter=QLineEdit()
        self.Converter.setPlaceholderText('Paste BCH address here and press button below, to convert it to P2SH, enabling sigscript malleability.')
        self.Converter.setToolTip('Default receiving address is default.\nPressing spacebar etc can correct the Script below.')
        self.Converter.textChanged.connect(self.ScriptGen)
                
        self.AddrPattern=QLineEdit()
        self.AddrPattern.setPlaceholderText('(Optional) CashAddr pattern. Vanity-Generator for P2SH addresses.')
        self.AddrPattern.setToolTip("2nd digit's worth 2b & the rest are 5b each.\nq₃₂==0 & pqqqqqq...↔0000000... \nCashAddr digits are:\n"+self.BCH32+'\n'+self.BCH32.swapcase()+'\nClear this box to re-generate old VanityTXID addresses from before v1.5.')  #₃₂ means base 32.
        self.AddrPattern.setMaxLength(16)   #With 8B nonce probably won't reach 16 CashAddr chars (difficulty 32**14*4/16**16=256x harder).
        
        self.P2SHDifficulty = QLabel()
        self.P2SHDifficulty.setToolTip('Difficulty estimate, in MH.\nSHA256 difficulty increases with Script size, but not RIPEMD160 difficulty.')
        self.AddrPattern.textChanged.connect(self.P2SHDifficultyChanged)
        self.AddrPattern.setText('pqqqqq')
        HBoxAddrPattern = QHBoxLayout()
        {HBoxAddrPattern.addWidget(Widget) for Widget in (self.AddrPattern, self.P2SHDifficulty)}
        
        self.Script=QLineEdit()
        self.Script.setPlaceholderText('Enter any contract Script here (510B limit), enter CashAddr Pattern above, and press Generate button below to generate a contractual vanity address.')
        self.Script.setMaxLength(510*2)  #510B limit for Script input (output has +10B for VanityP2SH).
        self.Script.setToolTip("Editing this is risky. This is the contract.\n510B limit (1020 digits).")
        self.Converter.setText(window.wallet.get_receiving_address().to_ui_string())    #Display VanityTXID Script for receiving_address.
        self.BoxReadOnly.setChecked(True)
        
        self.NoncePosBox = QComboBox()
        self.NoncePosBox.addItems('<Nonce>DROP @'+Str for Str in 'Start End'.split())
        self.NoncePosBox.setCurrentIndex(1)
        self.NoncePosBox.setToolTip('Nonce position.\nVanityTXID requires nonce at end, for simplicity.\nShould be placed before OP_CODESEPARATOR.\nA Contract state is usually at the start.')
        HBoxScript = QHBoxLayout()
        {HBoxScript.addWidget(Widget) for Widget in (self.Script, self.NoncePosBox)}
        
        VBoxAddresses=QVBoxLayout()
        VBoxAddresses.addLayout(HBoxAddresses), VBoxAddresses.addWidget(self.Converter)
        {VBoxAddresses.addLayout(HBox) for HBox in (HBoxAddrPattern, HBoxScript)}
        HBoxP2SH=QHBoxLayout()
        {HBoxP2SH.addLayout(VBox) for VBox in (VBoxAddressesLabels, VBoxAddresses)}

        self.TXBox = QPlainTextEdit()
        self.TXBox.setPlaceholderText("Paste raw TX hex here for inputs to be signed by this wallet wherever possible. It's TXID is then generated for the starting pattern below. Pattern & Message can be left blank, in which case the TXID can be generated on a separate PC. Remember to set a higher fee in the watching-only wallet, e.g. 0.3 bits extra. The fee depends on message size.")

        self.TextHex, self.TextHexIndex = QComboBox(), 0    #TextHexIndex remembers whether (text) or (hex).
        self.TextHex.addItems(('(text) (hex)').split())
        self.TextHex.activated.connect(self.HexConverter), self.TextHex.highlighted.connect(self.TextHexHighlighted)
        VBoxType=QVBoxLayout()
        {VBoxType.addWidget(Widget) for Widget in (QLabel('(hex)'), self.TextHex)}

        PatternLabel=QLabel('TXID Starting Pattern: ')
        MessageLabel=QLabel('Sigscript Message: ')
        VBoxLabels=QVBoxLayout()
        {VBoxLabels.addWidget(Label) for Label in (PatternLabel, MessageLabel)}
        
        self.TXIDPattern=QLineEdit()
        self.TXIDPattern.setMaxLength(32)  #With 8 Byte nonce, unlikely to get more than 16.
        self.TXIDPattern.setPlaceholderText('(Optional) Enter starting pattern for TXID.')
        self.TXIDDifficulty = QLabel()
        self.TXIDDifficulty.setToolTip('Difficulty estimate, in MH.\nSHA256d difficulty increases with TX & Message size.')
        self.TXIDPattern.textChanged.connect(self.TXIDDifficultyChanged)
        self.TXIDPattern.setText('00000')
        HBoxTXIDPattern=QHBoxLayout()
        {HBoxTXIDPattern.addWidget(Widget) for Widget in (self.TXIDPattern, self.TXIDDifficulty)}
        
        self.Message=QLineEdit()
        self.Message.setPlaceholderText('(Optional) Enter message. It appears first in all the newly created sigscripts.')
        self.Message.setMaxLength(self.MaxMessage)
        self.MessageCount = QLabel('0B')
        self.MessageCount.setToolTip('Message size.\n520 Byte limit.')
        self.Message.textChanged.connect(self.MessageChanged)
        HBoxMessage = QHBoxLayout()
        {HBoxMessage.addWidget(Widget) for Widget in (self.Message, self.MessageCount)}
        
        VBoxConfig=QVBoxLayout()
        {VBoxConfig.addLayout(HBox) for HBox in (HBoxTXIDPattern, HBoxMessage)}
        
        HBoxConfig=QHBoxLayout()
        {HBoxConfig.addLayout(Layout) for Layout in (VBoxType, VBoxLabels, VBoxConfig)}
   
        self.TTSLen=QComboBox()
        self.TTSLen.addItems('Pronounce '+str(Len) for Len in range(1,65))
        self.TTSLen.setCurrentIndex(15)
        self.TTSLen.setToolTip('Max # of digits to pronounce.')
        
        self.TTSRate=QComboBox()
        self.TTSRate.addItems('@ Rate '+str(Rate) for Rate in range(11))
        self.TTSRate.setCurrentIndex(5)
        self.TTSRate.setToolTip('On POSIX 175*(450/175)**(Rate/10) WPM')
        
        self.ThreadsBox=QComboBox()
        self.ThreadsBox.addItem('1 Thread'), self.ThreadsBox.addItems(str(N)+' Threads' for N in range(2,257))
        self.ThreadsBox.setCurrentIndex(shutil.os.cpu_count()-1)
        self.ThreadsBox.setToolTip("Default is .cpu_count().\nMore Threads won't increase hash rate.")
        
        self.TTSBox=QCheckBox('TTS')
        self.TTSBox.setChecked(True)
        self.TTSBox.setToolTip('Text-To-Speech (Address & TXID)\nOn Linux requires espeak.')
        self.TTSBox.toggled.connect(self.toggledTTS)
        self.l337=QCheckBox('1337')
        self.l337.setToolTip(".translate(dict(zip(map(ord,'0123456789'),'OlZEASGTBP')))")
        HBoxTTS=QHBoxLayout()
        {HBoxTTS.addWidget(Widget) for Widget in (self.TTSBox, self.TTSLen, self.TTSRate, self.l337)}   #All TTS options should go together. I'm starting to like 'for' loops done in reverse.
        
        self.notify=QCheckBox('.notify')
        self.notify.setToolTip('.notify & .activateWindow when finished.')
        self.RateLabel=QLabel('_.______ MH/s · _.___ s')
        self.RateLabel.setToolTip("Mega Hashes per second · seconds\nEach Hash is a double hash, for TXID & P2SH generating.\nFor TXID, the 2nd hash's input is much smaller than the 1st.\nTXID SHA-256d are usually much slower than SHA-256→RIPEMD-160, except for large Scripts.")

        HBoxOptions=QHBoxLayout()
        HBoxOptions.addLayout(HBoxTTS)
        {HBoxOptions.addWidget(Widget) for Widget in (self.notify,self.ThreadsBox,self.RateLabel)}
        
        {Label.setAlignment(Qt.AlignRight | Qt.AlignVCenter) for Label in {AddressesLabel,ConverterLabel,AddrPatternLabel,ScriptLabel,PatternLabel,MessageLabel}}
        {Label.setTextInteractionFlags(Qt.TextSelectableByMouse) for Label in {Title,AddressesLabel,ConverterLabel,AddrPatternLabel,ScriptLabel,PatternLabel,MessageLabel,self.RateLabel, self.HashDifficulty, self.P2SHDifficulty, self.TXIDDifficulty, self.MessageCount}}     #Copy-pasteable labels.
        
        VBox = QVBoxLayout()
        {VBox.addLayout(HBox) for HBox in (HBoxTitle, HBoxHash)}
        VBox.addWidget(self.Buttons[2]), VBox.addLayout(HBoxP2SH)
        {VBox.addWidget(Widget) for Widget in (self.Buttons[1], self.TXBox)}
        VBox.addLayout(HBoxConfig), VBox.addWidget(self.Buttons[0]), VBox.addLayout(HBoxOptions)
        
        self.setLayout(VBox)
        window.addr_converter_button.clicked.connect(self.CashAddrToggled)   #Toggle CashAddr.
             
        self.Movies=[QMovie(WebP) for WebP in plugin.WebPButtons]
        {self.Movies[n].frameChanged.connect((self.setIcon0, self.setIcon1, self.setIcon2)[n]) for n in (0,1,2)}
        {Mov.start()         for Mov in self.Movies}
        {Mov.setPaused(True) for Mov in self.Movies}
    def clickedTXID(self):
        window=self.window
        Message=self.Message.text()
        if not self.TextHexIndex: Message=Message.encode().hex()[:self.MaxMessage*2]
        elif len(Message)%2: #Append 0 if someone wants an odd hex Message.
            self.Message.insert('0')
            Message+='0'
        Pattern=self.TXIDPattern.text()
        if not all(Char in '0123456789ABCDEFabcdef' for Char in Pattern):
            window.show_message("Invalid hex Pattern.\nOnly '0123456789ABCDEFabcdef' characters are allowed.")
            return
        TX=electroncash.Transaction(self.TXBox.toPlainText())
        try: TX.inputs()[0] and TX.outputs()    #Valid hex in text box?
        except:
            window.show_message("Invalid TX.\nClicking on 'Example' provides a quick test.")
            return
        wallet=window.wallet
        Password=None
        for InputN in range(len(TX.inputs())):   # Sign all VanityTXID inputs, whenever possible.
            Input=TX.inputs()[InputN]
            if Input['signatures']!=[None]: continue    #Already signed.
            
            try: script,P2PKHaddress=self.UIdict[Input['address']]
            except: continue    #Can't sign this input using VanityTXID

            Input['type']='unknown'
            Input['scriptCode']=script
            
            PrivKey=None
            if not wallet.has_password(): PrivKey=bytearray(bitcoin.deserialize_privkey(wallet.export_private_key(P2PKHaddress,None))[1])
            while PrivKey is None:  #Need loop to get the right password.
                if not Password:
                    try: Password=bytearray(window.password_dialog().encode())    #A bytearray is mutable, and may be easier to erase (more secure) than an immutable str.
                    except: return #User cancelled, since None can't be encoded.
                try: PrivKey=bytearray(bitcoin.deserialize_privkey(wallet.export_private_key(P2PKHaddress,Password.decode()))[1])
                except: Password=None   #Bad Password.
            if wallet.is_schnorr_enabled(): Sig=electroncash.schnorr.sign(bytes(PrivKey),bitcoin.Hash(bitcoin.bfh(TX.serialize_preimage(InputN))))
            else: Sig=TX._ecdsa_sign(bytes(PrivKey),bitcoin.Hash(bitcoin.bfh(TX.serialize_preimage(InputN))))
            PrivKey[0:]=bytearray(len(PrivKey)) #Erase PrivKey with \x00 bytes.
            del PrivKey
            Input['scriptSig']=push_script(Message)+'00'+push_script(Sig.hex()+'41')+push_script(script)
        while wallet.can_sign(TX):  #Also sign using standard wallet. Need a loop to get the right password. There's an issue where we fail to add a Message to nothing but a simple P2PKH input.
            TX.set_sign_schnorr(wallet.is_schnorr_enabled())
            if not wallet.has_password(): wallet.sign_transaction(TX,None)
            elif not Password:
                try: Password=bytearray(window.password_dialog().encode())
                except: return #User cancelled.
            try: wallet.sign_transaction(TX,Password.decode())
            except: Password=None    #Bad Password.
        if Password: Password[0:]=bytearray(len(Password))   #Erase Password, when correct.
        del Password
        gc.collect()    #Garbage Collector for PrivKey & Password memory allocation.
        TX=electroncash.Transaction(TX.serialize())
          
        if not Pattern or not TX.is_complete():
            window.show_transaction(TX)     #Empty Pattern or more sigs needed -> return.
            return
        for Input in TX.inputs():   # Determine nonce position. Finding 'ac7777' is a shortcut to a full script analysis of P2SH inputs, which just takes even more code.
            if Input['type']=='unknown' and 'ac7777' in Input['scriptSig']:
                SigScript=Input['scriptSig']
                MessageSize=int(SigScript[0:2],16)
                SigScript=SigScript[2:]
                if MessageSize==0x4c:   #OP_PUSHDATA1
                    MessageSize=int(SigScript[0:2],16)
                    SigScript=SigScript[2:]
                elif MessageSize==0x4d: #OP_PUSHDATA2
                    MessageSize=int(bitcoin.rev_hex(SigScript[0:4]),16)
                    SigScript=SigScript[4:]
                SigScript=SigScript[2*MessageSize:]
                NonceSize=int(SigScript[0:2],16)
                SigScript=SigScript[2+2*NonceSize:]
                Input['scriptSig']=push_script(Message)+'08'+'00'*8+SigScript
                break
        TX=electroncash.Transaction(TX.serialize())
        try: NoncePos=int(TX.raw.find(SigScript)/2)-8 #00 threads corresponds to just 1. 3 Byte nonce position can handle large TX.
        except:
            window.show_message("TX.is_complete() but no VanityTXID inputs detected.")
            return
        ThreadsN=self.ThreadsBox.currentIndex()+1
        self.Popen([self.plugin.exe[0],bitcoin.int_to_hex(ThreadsN-1),bitcoin.rev_hex(bitcoin.int_to_hex(NoncePos,3)),Pattern,TX.raw],0)
        self.Thread[0]=threading.Thread(target=self.communicateTXID)
        self.Thread[0].start()
        self.Buttons[0].clicked.disconnect(), self.Buttons[0].clicked.connect(self.process[0].terminate), self.Buttons[0].setText('.terminate')
        self.Movies[0].setPaused(False)
    def communicateTXID(self):
        Time=time.time()    #I've verified there's no time delay from starting this thread.
        communicate=self.process[0].communicate()[0]
        Time=time.time()-Time

        self.Buttons[0].clicked.disconnect(), self.Buttons[0].clicked.connect(self.clickedTXID), self.Buttons[0].setText(self.ButtonText[0])
        self.Movies[0].setPaused(True)
        if not communicate: return  #.terminate occurred.
        
        TX,Nonces=communicate.decode().split()
        TXID=electroncash.Transaction(TX).txid_fast()
        if self.notify.isChecked():
            window=self.window
            window.notify(TXID), window.activateWindow()
        self.HiddenBoxes[0].setPlainText(TX)
        self.RateLabel.setText(str(round(int(Nonces,16)/1e6/Time,6))+' MH/s · '+str(round(Time,3))+' s')
        self.TTS(TXID)
    def show_transaction(self): self.window.show_transaction(electroncash.Transaction(self.HiddenBoxes[0].toPlainText()))    #.show_message is also possible here.
    def SearchContacts(self):
        wallet=self.window.wallet
        self.AddressLine.clear()
        try:
            for Contact in wallet.contacts.get_all():
                try:
                    Script=Contact.name.split()[0]
                    ContactAddress=electroncash.address.Address.from_string(Contact.address)
                    if ContactAddress!=ContactAddress.from_multisig_script(bitcoin.bfh(Script)): continue #address must match Script.
                except: continue
                P2PKHaddress=self.IsOurScript(Script)
                if not P2PKHaddress: continue
                self.UIdict[ContactAddress]=Script,P2PKHaddress
                self.AddressLine.insert(Contact.address+' ')
        except: #EC-v3.6.6 backwards compatibility.
            for Key in wallet.contacts.keys():
                try:
                    Script=wallet.contacts[Key][1].split()[0]
                    ContactAddress=electroncash.address.Address.from_string(Key)
                    if ContactAddress!=ContactAddress.from_multisig_script(bitcoin.bfh(Script)): continue #address must match Script.
                except: continue
                P2PKHaddress=self.IsOurScript(Script)
                if not P2PKHaddress: continue
                self.UIdict[ContactAddress]=Script,P2PKHaddress
                self.AddressLine.insert(Key+' ')
    def TextHexHighlighted(self,Index): self.TextHex.setCurrentIndex(Index), self.HexConverter()    #highlighted→activated
    def HexConverter(self): #Convert Message between (text) & (hex).
        Index = self.TextHex.currentIndex()
        if Index == self.TextHexIndex: return   #Do nothing if not toggling.
        self.TextHexIndex, Text = Index, self.Message.text()   #Remember Index for next time.
        if Index: self.Message.setMaxLength(self.MaxMessage*2), self.Message.setText(Text.encode().hex())   #→(hex)
        else:   #→(text)
            try: self.Message.setText(bitcoin.bfh(Text).decode()), self.Message.setMaxLength(self.MaxMessage)
            except: #Remain (hex).
                self.TextHex.setCurrentIndex(1)
                self.TextHexIndex = 1
    def toggledTTS(self): {Box.setEnabled(self.TTSBox.isChecked()) for Box in {self.TTSLen,self.TTSRate,self.l337}}
    def Example(self):
        self.TXBox.setPlainText('0100000001c73bbd847861d7b30ee87ef9bf0bd40824ee1b44c0e4c2832b6b438e185c3412000000007c0008060000000001a6794163314eac47fb93402b28a9ebdef00d687dcf85c399593cd248b57c30419814c80df637003b8db1aabc5f0ea3bfd0819bda30fc57b32401c39a5f54a47cf51dbc412f21039eb296a68925e890502b54881b220bb108d1c0676236a3180d5eb398e81c4f90ac77770805000000008f5d9c75feffffff01c57f00000000000017a91400000009e62dc2a3eafd18b870ed16fff020a69d87a4e90a00')
        self.TXIDPattern.setText('abcde')
        self.Message.clear()
        self.clickedTXID()
    def clickedP2SH(self):
        Pattern=self.AddrPattern.text()
        BCH32=self.BCH32+self.BCH32.swapcase()
        window=self.window
        if not all([Char in BCH32 for Char in Pattern]) or Pattern and Pattern[0] not in 'pP' or len(Pattern)>1 and Pattern[1] not in 'qpzrQPZR':
            window.show_message("Invalid P2SH CashAddr Pattern.\nMust start with 'p' or 'P'.\n2nd char must be chosen from 'qpzrQPZR'.\nAll chars must be from '"+BCH32+"'.")
            return
        Script=self.Script.text()
        if len(Script)%2 or not all(Char in '0123456789ABCDEFabcdef' for Char in Script):
            window.show_message("Invalid Script.")
            return
        if Pattern in {'','p','P'}: #No vanity address (old VanityTXID).
            self.AddContactVerify(Script)
            return
        Nonce='08'+'00'*8+'75'  #'75'=OP_DROP
        if self.NoncePosBox.currentIndex(): #Nonce @End.
            NoncePos=len(Script)//2+1
            Script+=Nonce
        else:   #Nonce @Start.
            NoncePos=1  #08 1st.
            Script=Nonce+Script
        ThreadsN=self.ThreadsBox.currentIndex()+1
        self.Popen([self.plugin.exe[1],bitcoin.int_to_hex(ThreadsN-1),bitcoin.rev_hex(bitcoin.int_to_hex(NoncePos,2)),Pattern,Script],1) #2 Byte nonce position can handle large Script.
        self.Thread[1]=threading.Thread(target=self.communicateP2SH)
        self.Thread[1].start()
        self.Buttons[1].clicked.disconnect(), self.Buttons[1].clicked.connect(self.process[1].terminate), self.Buttons[1].setText('.terminate')
        self.Movies[1].setPaused(False)
    def communicateP2SH(self):
        Time=time.time()    #I've verified there's no time delay from starting this thread.
        communicate=self.process[1].communicate()[0]
        Time=time.time()-Time

        self.Buttons[1].clicked.disconnect(), self.Buttons[1].clicked.connect(self.clickedP2SH), self.Buttons[1].setText(self.ButtonText[1])
        self.Movies[1].setPaused(True)
        if not communicate: return  #.terminate occurred.
        
        Script,Nonces=communicate.decode().split()
        Address=electroncash.address.Address.from_multisig_script(bitcoin.bfh(Script)).to_ui_string()
        if self.notify.isChecked():
            window=self.window
            window.notify(Address), window.activateWindow()
        self.AddContactVerify(Script)
        self.RateLabel.setText(str(round(int(Nonces,16)/1e6/Time,6))+' MH/s · '+str(round(Time,3))+' s')
        self.TTS(Address)
    def ShowMessageBox(self): 
        self.SearchContacts()   #Linux requires .SearchContacts() is executed only by the primary Qt thread.
        Box=QMessageBox()
        Box.setInformativeText("Above are the vanity address & its Script.\nPress 'Show Details...' to Copy the full Script etc.\nMoney sent to this address may be lost if a mistake has been made.\nIf a VanityTXID Script belonging to this wallet, all details are saved as a Contact.\nThen, after sending a coin to the address, import it into a watching-only wallet & use the Send→Preview→Copy buttons to obtain the TX hex needed for VanityTXID in this wallet.")
        Box.setText(self.HiddenBoxes[1].toPlainText()), Box.setDetailedText(self.HiddenBoxes[1].toPlainText()), Box.setTextInteractionFlags(Qt.TextSelectableByMouse), Box.exec()    #.show_full_ui_string() is another possibility, but the bitcoincash: prefix gets in the way.
    def ScriptGen(self):
        for Word in self.Converter.text().split():   #Loop over inputs until a good address is found.
            try:
                Address=electroncash.address.Address.from_string(Word)
                PubKey=self.window.wallet.get_public_key(Address)   #If multisig address, return nothing since that'd require "get_public_keys" (not supported)
            except: continue
            try:    script= push_script(PubKey)+'ac7777'    #'77'=OP_NIP This line applies to standard wallet addresses. Output begins with '21'.
            except: script=PubKey.to_script_hex()+'7777'    #Imported private key/s wallet. PubKey isn't a string, but an object of length 1, whose script already has 'ac'=OP_CHECKSIG at the end. Output begins with either 21 or 41.
            self.Script.setText(script)
            return
    def IsOurScript(self,Script):
        try:
            PKEnd=2*(int(Script[0:2],16)+1)
            P2PKHaddress=electroncash.address.Address.from_pubkey(Script[2:PKEnd])
            if P2PKHaddress in self.window.wallet.get_addresses():
                if Script[PKEnd:PKEnd+8]=='ac777708' and Script.endswith('75') and len(Script)==PKEnd+26: return P2PKHaddress    #Return signing address if the wallet has it.
                elif Script.endswith('ac7777') and len(Script)==PKEnd+6: return P2PKHaddress   #VanityTXID address, but not a vanity address. (v1.0.0-v1.4.1) These save 10B on every txn, due to the 8B nonce.
            else: return
        except: return
    def AddContactVerify(self,Script):
        P2SHaddress=electroncash.address.Address.from_multisig_script(bitcoin.bfh(Script)).to_ui_string()
        P2PKHaddress=self.IsOurScript(Script)
        if P2PKHaddress:
            window=self.window
            wallet=window.wallet
            Name=Script+' VANITYTXID SCRIPT FROM '+P2PKHaddress.to_ui_string()
            try:    wallet.contacts.add(electroncash.contacts.Contact(Name,P2SHaddress,'address'),unique=True)
            except: wallet.contacts[P2SHaddress]=('address',Name) #EC-v3.6.6 backwards compatibility.
            window.update_wallet()    #Refresh GUI Contacts
        self.HiddenBoxes[1].setPlainText(P2SHaddress+'\n'+Script)
    def TTS(self,Text):
        if not self.TTSBox.isChecked(): return
        Text=Text[:self.TTSLen.currentIndex()+1]    #Works even if 64>Address length.
        if self.l337.isChecked(): Text=Text.translate(dict(zip(map(ord,'0123456789'),'OlZEASGTBP')))
        if 'Windows' in platform.system(): subprocess.Popen(['PowerShell','-C',"$V=New-Object -C SAPI.SPVoice;$V.Rate="+str(self.TTSRate.currentIndex())+";$V.Voice=$V.GetVoices().Item("+str(random.getrandbits(1))+");$V.Speak('"+Text+"')"],creationflags=0x8000000)  #A faster more complicated alternative is to pre-launch PowerShell. MSHTA isn't allowed on 32-bit WIN10 Home N. 
        else:
            WPM=str(round(175*(450/175)**(self.TTSRate.currentIndex()/10)))   #Compute non-linear Words-Per-Minute on POSix. 175->450 WPM. 450WPM max is specified by espeak.
            if 'Darwin' in platform.system():
                Voices='Rishi Veena Moira Fiona Tessa Daniel Samantha Victoria Alex Fred'   #English only.
                #Voices='Ting-Ting Sin-Ji'  #macOS users can pick a specific language here, e.g. Chinese.
                #Voices='Daniel Alex Fred Samantha Victoria Tessa Fiona Karen Maged Ting-Ting Sin-Ji Mei-Jia Zuzana Sara Ellen Xander Rishi Veena Moira Satu Amelie Thomas Anna Melina Mariska Damayanti Alice Luca Kyoko Yuna Nora Zosia Luciana Joana Ioana Milena Yuri Laura Diego Paulina Juan Jorge Monica Alva Kanya Yelda'    #Uncomment this line to hear any language/accent.
                subprocess.Popen(['say','-v',random.choice(Voices.split()),'-r',WPM,Text])
            else:
                try: subprocess.Popen(['espeak','-s',WPM,'-p',str(random.choice(range(100))),Text]) # espeak required on Linux to hear TTS. sudo apt install espeak. Random -p pitch.
                except: self.TTSBox.setChecked(False)
    def clickedHash(self):
        if not self.Paths:
            self.Paths=QFileDialog().getOpenFileNames()[0]
            if not self.Paths: return #User cancelled.
        self.Thread[2]=threading.Thread(target=self.communicateHash)
        self.Thread[2].start()
        self.Buttons[2].clicked.disconnect(), self.Buttons[2].clicked.connect(self.terminateHash), self.Buttons[2].setText('.terminate')
        self.Movies[2].setPaused(False)
    def communicateHash(self):
        window=self.window
        for Path in self.Paths:
            Pattern=self.HashPattern.text()
            if not Pattern or not all(Char in '0123456789ABCDEFabcdef' for Char in Pattern):    #Invalid Pattern.
                time.sleep(0.1) #It takes time for the Button to connect, before it then disconnects again.
                self.HiddenBoxes[2].setPlainText("Invalid or empty hex Pattern.\nOnly characters from '0123456789ABCDEFabcdef' are allowed.")
                break
            ThreadsN=self.ThreadsBox.currentIndex()+1
            
            Dir=shutil.os.path.dirname(Path)+'/VanityHash/'
            if not shutil.os.path.exists(Dir): shutil.os.mkdir(Dir)
            PathOut=Dir+shutil.os.path.basename(Path)
            
            NonceTarget=self.NonceTargetBox.text()
            if NonceTarget: self.Popen([self.plugin.exe[2],bitcoin.int_to_hex(ThreadsN-1),Pattern,Path,PathOut,NonceTarget],2)
            else:           self.Popen([self.plugin.exe[2],bitcoin.int_to_hex(ThreadsN-1),Pattern,Path,PathOut            ],2)
            Time=time.time()
            communicate=self.process[2].communicate()[0]
            Time=time.time()-Time
            if not communicate: break  #.terminate occurred.
            
            Hash,Nonces=communicate.decode().split()
            if self.notify.isChecked(): window.notify(Hash), window.activateWindow()
            self.HiddenBoxes[2].setPlainText(Hash+"\nis the SHA256 Checksum of\n"+PathOut)
            self.RateLabel.setText(str(round(int(Nonces,16)/1e6/Time,6))+' MH/s · '+str(round(Time,3))+' s')
            self.TTS(Hash)
        self.Paths=None
        self.Movies[2].setPaused(True)
        self.Buttons[2].clicked.disconnect(), self.Buttons[2].clicked.connect(self.clickedHash), self.Buttons[2].setText(self.ButtonText[2])
    def show_message(self): self.window.show_message(self.HiddenBoxes[2].toPlainText())
    def setReadOnly(self): self.Script.setReadOnly(self.BoxReadOnly.isChecked())
    def dragEnterEvent(self,Event): Event.accept()  #Must 1st accept drag before drop.
    def dropEvent(self,Event):
        Event.accept()
        if self.process[2]: self.terminateHash()  # Drag & drop terminates current Hashing process.
        self.Paths=[URL.toLocalFile() for URL in Event.mimeData().urls()]
        self.clickedHash() 
    def setIcon0(self): self.Buttons[0].setIcon(QIcon(self.Movies[0].currentPixmap()))
    def setIcon1(self): self.Buttons[1].setIcon(QIcon(self.Movies[1].currentPixmap()))
    def setIcon2(self): self.Buttons[2].setIcon(QIcon(self.Movies[2].currentPixmap()))
    def terminateHash(self): self.process[2].terminate(), self.Thread[2].join() #Looping over many files using a sub-thread causes an issue because that thread isn't allowed to directly connect a button to .terminate().
    def Popen(self,Command,n):
        if 'Windows' in platform.system():  self.process[n]=subprocess.Popen(Command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,creationflags=0x8000000|0x4000)  #CREATE_NO_WINDOW|BELOW_NORMAL_PRIORITY_CLASS
        else:                               self.process[n]=subprocess.Popen(Command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
    def HashDifficultyChanged(self): self.HashDifficulty.setText(str(round(16**len(self.HashPattern.text())/1e6,6))+' MH Difficulty.    Nonce target:')
    def P2SHDifficultyChanged(self):
        Len = len(self.AddrPattern.text())
        if   Len <2: Difficulty = 1
        elif Len==2: Difficulty = 4
        else:        Difficulty = 4*32**(Len-2)
        self.P2SHDifficulty.setText(str(round(Difficulty/1e6,6))+' MH Difficulty')
    def TXIDDifficultyChanged(self): self.TXIDDifficulty.setText(str(round(16**len(self.TXIDPattern.text())/1e6,6))+' MH Difficulty')
    def CashAddrToggled(self):
        try: self.Converter.setText(electroncash.address.Address.from_string(self.Converter.text()).to_ui_string()) #Toggle address in converter line.
        except: pass
        try: self.AddressLine.setText(' '.join(electroncash.address.Address.from_string(Address).to_ui_string() for Address in self.AddressLine.text().split())) #Toggle VanityTXID addresses.
        except: pass
    def MessageChanged(self):
        Text = self.Message.text()
        if self.TextHexIndex:
            if not all(Char in '0123456789ABCDEFabcdef' for Char in Text):    #Forcibly switch to (text).
                self.TextHexIndex = 0
                self.TextHex.setCurrentIndex(0), self.MessageChanged()
                return
            Size = len(Text)//2 + len(Text)%2   #Round up the # of Bytes. 
        else: Size = len(Text.encode())  #e.g. 字 is 3B.
        self.MessageCount.setText(str(Size)+'B')
