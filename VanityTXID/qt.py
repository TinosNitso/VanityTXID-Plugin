from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QMovie
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPlainTextEdit, QPushButton, QCheckBox, QComboBox
from electroncash.i18n import _ #Language translator doesn't work on more than one word at a time, at least not when I tested it.
from electroncash.plugins import BasePlugin, hook
import electroncash, subprocess, threading, zipfile, shutil, gc, random, binascii, time, platform
from electroncash import bitcoin

class Plugin(BasePlugin):
    def __init__(self, parent, config, name):
        BasePlugin.__init__(self, parent, config, name)
        self.windows, self.tabs, self.UIs = {}, {}, {}  #Initialize plugin wallet "dictionaries".
        
        Dir=self.parent.get_external_plugin_dir()+'/VanityTXID/'
        self.WebP=Dir+'bin/Icon.webp'    #QMovie only supports GIF & WebP. GIF appears ugly.
        if shutil.os.path.exists(Dir): Extract=False   #Only ever extract zip (i.e. install) once.
        else:
            Extract=True
            Zip=zipfile.ZipFile(Dir[:-1]+'-Plugin.zip') #shutil._unpack_zipfile is an alternative function, but it'd extract everything.
            Zip.extract('bin/Icon.webp',Dir), Zip.extract('bin/LICENSE.txt',Dir)
        if 'Windows' in platform.system():
            if '64' in platform.machine():  binDir='bin/Windows/'
            else:                           binDir='bin/Windows-x86/'
            self.exeTXID , self.exeP2SH = Dir+binDir+'VanityTXID-Plugin.exe' , Dir+binDir+'VanityP2SH-Plugin.exe'
            if Extract: {Zip.extract(Item,Dir) for Item in Zip.namelist() if Item.startswith(binDir)}
        else:
            binDir='bin/'+platform.system()+'/'
            self.exeTXID , self.exeP2SH = Dir+binDir+'VanityTXID-Plugin' , Dir+binDir+'VanityP2SH-Plugin'
            if Extract:
                for exe in {self.exeTXID,self.exeP2SH}: Zip.extract(exe.lstrip(Dir),Dir), subprocess.Popen(['chmod','+x',exe])
        if Extract: Zip.close()
        self.Icon=QIcon()   #QMovie waits for init_qt.
    def on_close(self):
        """BasePlugin callback called when the wallet is disabled among other things."""
        del self.Movie, self.Icon, self.WebP, self.exeTXID, self.exeP2SH
        for window in self.windows.values(): self.close_wallet(window.wallet)
        shutil.rmtree(self.parent.get_external_plugin_dir()+'/VanityTXID')
    @hook
    def init_qt(self, qt_gui):
        """Hook called when a plugin is loaded (or enabled)."""
        if self.UIs: return # We get this multiple times.  Only handle it once, if unhandled.
        self.Movie=QMovie(self.WebP)    
        self.Movie.frameChanged.connect(self.setTabIcon), self.Movie.start()
        for window in qt_gui.windows: self.load_wallet(window.wallet, window)           # These are per-wallet windows.
    @hook
    def load_wallet(self, wallet, window):
        """Hook called when a wallet is loaded and a window opened for it."""
        wallet_name = wallet.basename()
        self.windows[wallet_name] = window
        l = UI(window, self)
        tab = window.create_list_tab(l)
        self.tabs[wallet_name],self.UIs[wallet_name] = tab,l
        window.tabs.addTab(tab,self.Icon, 'VanityTXID') #Add Icon instantly in case WebP frame rate is slow.
    @hook
    def close_wallet(self, wallet):
        wallet_name = wallet.basename()
        try:
            try: self.UIs[wallet_name].processTXID.terminate() #Can't assume successful .terminate when disabling.
            except: pass
            self.UIs[wallet_name].processP2SH.terminate()
        except:     pass
        del self.UIs[wallet_name]   #Delete UI now to stop Movie's tab connection, before tab removed.
        window = self.windows[wallet_name]
        window.tabs.removeTab(window.tabs.indexOf(self.tabs[wallet_name]))
        del self.tabs[wallet_name]
    def setTabIcon(self):
        self.Icon.addPixmap(self.Movie.currentPixmap())
        for wallet_name in self.UIs.keys():
            Tabs=self.windows[wallet_name].tabs
            Tabs.setTabIcon(Tabs.indexOf(self.tabs[wallet_name]),self.Icon)
class UI(QDialog):
    MaxMessage=520 #Other languages like Chinese require a few bytes per character.
    ButtonTextTXID=_('Sign TX and/or Mine TXID')
    ButtonTextP2SH=_('Generate Address')
    
    def __init__(self, window, plugin):
        QDialog.__init__(self, window)
        self.window=window
        self.plugin=plugin
        self.UIdict={}   #Store all VanityTXID addresses in a dictionary. This dict is used to ask wallet for private key/s when needed. Has form {P2SH: Script,P2PKH}. Updated using Search button etc.

        Title=QLabel('VanityTXID v1.5.0 (+VanityP2SH)')
        Title.setStyleSheet('font-weight: bold')
        Title.setAlignment(Qt.AlignCenter)
        
        Example = QPushButton(_('Example'))
        Example.clicked.connect(self.Example)
        
        HBoxTitle=QHBoxLayout()
        HBoxTitle.addWidget(Title,1)
        HBoxTitle.addWidget(Example,.1)

        AddressesLabel=QLabel(_('VanityTXID Addresses: '))
        ConverterLabel=QLabel(_('Address to Convert: '))
        AddrPatternLabel=QLabel(_('CashAddr Starting Pattern: '))
        ScriptLabel=QLabel(_('(hex) Script: '))
        VBoxAddressesLabels=QVBoxLayout()
        for Label in [AddressesLabel,ConverterLabel,AddrPatternLabel,ScriptLabel]: VBoxAddressesLabels.addWidget(Label)
        
        self.AddressLine=QLineEdit()
        self.AddressLine.setReadOnly(True)
        self.SearchContacts()
        self.AddressLine.setToolTip(_('Only these addresses can definitely be signed for. Not necessarily all contacts & contracts.'))
        SearchButton=QPushButton(_('Search Contacts'))
        SearchButton.clicked.connect(self.SearchContacts)
        HBoxAddresses=QHBoxLayout()
        HBoxAddresses.addWidget(self.AddressLine)
        HBoxAddresses.addWidget(SearchButton)

        self.Converter=QLineEdit()
        self.Converter.setPlaceholderText(_('Paste BCH address here and press button below, to convert it to P2SH, enabling sigscript malleability.'))
        self.Converter.setToolTip(_('Default receiving address is default.'))
        self.Converter.textChanged.connect(self.ScriptGen)
                
        self.AddrPattern=QLineEdit()
        self.AddrPattern.setPlaceholderText(_('(Optional) CashAddr pattern. Vanity-Generator for P2SH addresses.'))
        self.AddrPattern.setText('pqqqqq')
        self.AddrPattern.setToolTip(_('''The leading p doesn't actually "exist" on the blockchain, only the digits after it do. For PoW, q=0.'''))
        self.AddrPattern.setMaxLength(16)   #With 8B nonce probably won't reach 16 CashAddr chars (difficulty 32**14*4/16**16=256x harder).
        
        self.Script=QLineEdit()
        self.Script.setPlaceholderText(_('Enter any valid contract Script here, enter CashAddr Pattern above, and press Generate button below to generate a contractual vanity address.'))
        self.Script.setMaxLength(1040)  #520B limit for Scripts.
        self.Script.setToolTip(_("Editing this is very risky. This is the contract."))
        self.Converter.setText(window.wallet.get_receiving_address().to_ui_string())    #Display VanityTXID Script for receiving_address.
        
        VBoxAddresses=QVBoxLayout()
        VBoxAddresses.addLayout(HBoxAddresses)
        VBoxAddresses.addWidget(self.Converter)
        VBoxAddresses.addWidget(self.AddrPattern)
        VBoxAddresses.addWidget(self.Script)
        
        HBox=QHBoxLayout()
        HBox.addLayout(VBoxAddressesLabels)
        HBox.addLayout(VBoxAddresses)

        self.ButtonP2SH=QPushButton(self.ButtonTextP2SH)
        self.ButtonP2SH.clicked.connect(self.clickedP2SH)

        self.TXBox = QPlainTextEdit()
        self.TXBox.setPlaceholderText(_("Paste raw TX hex here for inputs to be signed by this wallet wherever possible. It's TXID is then mined for the starting pattern below. Pattern & Message can be left blank, in which case the result can be mined on a separate PC. Remember to set a higher fee in the watching-only wallet preferences, like 1.2 sat/B. The fee depends on message size."))

        self.TextHex=QComboBox()
        self.TextHex.addItems(_('(text) (hex)').split())
        self.TextHex.activated.connect(self.HexConverter)
        VBoxType=QVBoxLayout()
        VBoxType.addWidget(QLabel(_('(hex)')))
        VBoxType.addWidget(self.TextHex)

        PatternLabel=QLabel(_('TXID Starting Pattern: '))
        MessageLabel=QLabel(_('Sigscript Message: '))
        VBoxLabels=QVBoxLayout()
        VBoxLabels.addWidget(PatternLabel)
        VBoxLabels.addWidget(MessageLabel)

        VBoxConfig=QVBoxLayout()
        self.PatternLine=QLineEdit('00000')
        self.PatternLine.setMaxLength(32)  #With 8 Byte nonce, unlikely to get more than 16.
        self.PatternLine.setPlaceholderText(_('(Optional) Enter starting pattern for TXID.'))
        VBoxConfig.addWidget(self.PatternLine)
        
        self.Message=QLineEdit()
        self.Message.setPlaceholderText(_('(Optional) Enter message. It appears first in all the newly created sigscripts. 520 Byte limit.'))
        self.Message.setMaxLength(self.MaxMessage)
        VBoxConfig.addWidget(self.Message)
        
        HBoxConfig=QHBoxLayout()
        HBoxConfig.addLayout(VBoxType)
        HBoxConfig.addLayout(VBoxLabels)
        HBoxConfig.addLayout(VBoxConfig)

        self.ButtonTXID = QPushButton(self.ButtonTextTXID)
        self.ButtonTXID.clicked.connect(self.clickedTXID)
        
        self.TTSLen=QComboBox()
        self.TTSLen.addItems('Pronounce '+str(Len) for Len in range(1,65))
        self.TTSLen.setCurrentIndex(15)
        self.TTSLen.setToolTip(_('Max # of digits to pronounce.'))
        
        self.TTSRate=QComboBox()
        self.TTSRate.addItems('@ Rate '+str(Rate) for Rate in range(11))
        self.TTSRate.setCurrentIndex(5)
        self.TTSRate.setToolTip('On POSIX 175*(450/175)**(Rate/10) WPM')
        
        self.ThreadsBox=QComboBox()
        self.ThreadsBox.addItems(str(N)+' Threads' for N in range(1,257))
        self.ThreadsBox.setCurrentIndex(shutil.os.cpu_count()-1)
        self.ThreadsBox.setToolTip(_("Please don't increase above the default .cpu_count() since that can cause a hang bug.\nAlso, hash rate computation assumes all threads are equal.\nDemonstrating the bugs is interesting."))
        
        self.TTSbox=QCheckBox(_('TTS'))
        self.TTSbox.setChecked(True)
        self.TTSbox.setToolTip(_('Text To Sound (Address & TXID)\nOn Linux requires espeak.'))
        self.TTSbox.toggled.connect(self.toggled)
        self.l337=QCheckBox('1337')
        self.l337.setToolTip(".translate(dict(zip(map(ord,'0123456789'),'OlZEASGTBP')))")
        
        self.notify=QCheckBox('.notify')
        self.notify.setToolTip(_('.notify & .activateWindow when finished.'))
        self.RateLabel=QLabel('_._____ MH/s · _.___ s')
        self.RateLabel.setToolTip(_("Mega double Hashes per second · seconds. The 2nd hash's input is smaller than the 1st.\nTXID hashes are much slower than address hashes."))

        HBoxOptions=QHBoxLayout()
        for Widget in [self.TTSbox,self.TTSLen,self.TTSRate,self.l337,self.notify,self.ThreadsBox,self.RateLabel]: HBoxOptions.addWidget(Widget)
        
        for Label in {AddressesLabel,ConverterLabel,AddrPatternLabel,ScriptLabel,PatternLabel,MessageLabel}: Label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        for Label in {Title,AddressesLabel,ConverterLabel,AddrPatternLabel,ScriptLabel,PatternLabel,MessageLabel,self.RateLabel}: Label.setTextInteractionFlags(Qt.TextSelectableByMouse)   #All Labels copy-pasteable.
        
        VBox = QVBoxLayout()
        VBox.addLayout(HBoxTitle)
        VBox.addLayout(HBox)
        VBox.addWidget(self.ButtonP2SH)
        VBox.addWidget(self.TXBox)
        VBox.addLayout(HBoxConfig)
        VBox.addWidget(self.ButtonTXID)
        VBox.addLayout(HBoxOptions)
        self.setLayout(VBox)
        
        self.HiddenBox=QPlainTextEdit()
        self.HiddenBox.textChanged.connect(self.show_transaction) #Hidden textbox allows primary Qt thread to show_transaction.
        self.HiddenBoxP2SH=QPlainTextEdit()
        self.HiddenBoxP2SH.textChanged.connect(self.show_message) #.show_message(Script)
    def clickedTXID(self):
        window=self.window
        Message=self.Message.text()
        if not self.TextHex.currentIndex(): Message=binascii.hexlify(Message.encode()).decode()[:self.MaxMessage*2]
        else:
            if not all([Char in '0123456789ABCDEFabcdef' for Char in Message]):
                window.show_message('Invalid hex Message. Text option would work.')
                return   #Valid Message hex?
            if len(Message)%2:
                self.Message.insert('0') #Add 0 if someone wants an odd hex Message.
                Message+='0'
        Pattern=self.PatternLine.text()
        if not all([Char in '0123456789ABCDEFabcdef' for Char in Pattern]):
            window.show_message("Invalid hex Pattern. Only '0123456789ABCDEFabcdef' characters are allowed.")
            return
        TX=electroncash.Transaction(self.TXBox.toPlainText())
        try: TX.inputs()[0] and TX.outputs()    #Valid hex in text box?
        except:
            window.show_message("Invalid TX. Clicking on 'Example' provides a quick test.")
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
            Input['scriptSig']=bitcoin.push_script(Message)+'00'+bitcoin.push_script(Sig.hex()+'41')+bitcoin.push_script(script)
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
                Input['scriptSig']=bitcoin.push_script(Message)+'08'+'00'*8+SigScript
                break
        TX=electroncash.Transaction(TX.serialize())
        try: NoncePos=int(TX.raw.find(SigScript)/2)-8
        except:
            window.show_message("TX.is_complete() but no VanityTXID inputs detected.")
            return
        ThreadsN=self.ThreadsBox.currentIndex()+1
        Command=[self.plugin.exeTXID,bitcoin.int_to_hex(ThreadsN-1),bitcoin.rev_hex(bitcoin.int_to_hex(NoncePos,3)),Pattern,TX.raw] #00 threads corresponds to just 1. 3 Byte nonce position can handle large TX.
        if 'Windows' in platform.system(): self.processTXID=subprocess.Popen(Command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,creationflags=0x8000000|0x4000)  #CREATE_NO_WINDOW|BELOW_NORMAL_PRIORITY_CLASS
        else: self.processTXID=subprocess.Popen(Command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
        threading.Thread(target=self.communicateTXID,args=[NoncePos*2,ThreadsN]).start()

        self.ButtonTXID.clicked.disconnect()
        self.ButtonTXID.clicked.connect(self.processTXID.terminate)
        self.ButtonTXID.setText('.terminate')
    def communicateTXID(self,HexPos,ThreadsN):
        Time=time.time()    #I've verified there's no time delay from starting this thread.
        TX=self.processTXID.communicate()[0].decode()
        Time=time.time()-Time

        self.ButtonTXID.clicked.disconnect()
        self.ButtonTXID.clicked.connect(self.clickedTXID)
        self.ButtonTXID.setText(self.ButtonTextTXID)

        try: TXID=electroncash.Transaction(TX).txid_fast()
        except: return  #.terminate occurred.
        
        if self.notify.isChecked():
            window=self.window
            window.notify(TXID), window.activateWindow()
        self.HiddenBox.setPlainText(TX)
        self.HashRate(TX[HexPos:HexPos+16],ThreadsN,Time)
        self.TTS(TXID)
    def show_transaction(self): self.window.show_transaction(electroncash.Transaction(self.HiddenBox.toPlainText()))    #.show_message is also possible here.
    def SearchContacts(self):
        wallet=self.window.wallet
        self.AddressLine.clear()
        for Contact in wallet.contacts.get_all():
            if Contact.type!='address': continue    #Not address.
            if not Contact.name: continue   #Empty .name where Script must be.
            Script=Contact.name.split()[0]
            try:    #Don't assume 'Script' is a Script.
                ContactAddress=electroncash.address.Address.from_string(Contact.address)
                if ContactAddress!=ContactAddress.from_multisig_script(bitcoin.bfh(Script)): continue #address must match Script.
            except: continue
            P2PKHaddress=self.IsOurScript(Script)
            if not P2PKHaddress: continue
            self.UIdict[ContactAddress]=Script,P2PKHaddress
            self.AddressLine.insert(Contact.address+' ')
    def HexConverter(self):
        if self.TextHex.currentIndex():
            self.Message.setMaxLength(self.MaxMessage*2)
            self.Message.setText(binascii.hexlify(self.Message.text().encode()).decode())
        else:
            try: self.Message.setText(bitcoin.bfh(self.Message.text()).decode())
            except: pass
            self.Message.setMaxLength(self.MaxMessage)
    def toggled(self): {Box.setEnabled(self.TTSbox.isChecked()) for Box in {self.TTSLen,self.TTSRate,self.l337}}
    def Example(self):
        self.TXBox.setPlainText('0100000001811a89e09c0e06d29d59c5b42432972b8b274212e439c5d77fe3a2c543000000000000007c000801000000000120154136dfa8821f2e7cb02e1edeadbe05ad963c900877b201986d38e2dc36f3a0456aef6794aea08d2a39958a86013c06a6a52191c905a6563c5b420d279e6ce3e2be412f21039eb296a68925e890502b54881b220bb108d1c0676236a3180d5eb398e81c4f90ac77770805000000008f5d9c75feffffff01fb3000000000000017a91400000009e62dc2a3eafd18b870ed16fff020a69d87b2e50a00')
        self.PatternLine.setText('12345')
        self.Message.clear()
        self.ThreadsBox.setCurrentIndex(shutil.os.cpu_count()-1)
        self.TTSbox.setChecked(True)
        self.clickedTXID()
    def clickedP2SH(self):
        Pattern=self.AddrPattern.text()
        BCH32='qpzry9x8gf2tvdw0s3jn54khce6mua7l'
        BCH32+=BCH32.swapcase()
        window=self.window
        if not all([Char in BCH32 for Char in Pattern]) or Pattern and Pattern[0] not in 'pP' or len(Pattern)>1 and Pattern[1] not in 'qpzrQPZR':
            window.show_message("Invalid P2SH CashAddr Pattern. Must start with 'p' or 'P'. 2nd char must be chosen from 'qpzrQPZR'. All chars must be from '"+BCH32+"'.")
            return
        Script=self.Script.text()
        if len(Script)%2 or not all([Char in '0123456789ABCDEFabcdef' for Char in Script]):
            window.show_message("Invalid Script.")
            return
        if Pattern in {'','p'}: #No vanity address (old VanityTXID).
            self.AddContactVerify(Script)
            return
        Nonce='08'+'00'*8+'75'  #'75'=OP_DROP Addition to arbitrary Script. 
        Script+=Nonce
        NoncePos=int(Script.find(Nonce)/2)+1
        
        ThreadsN=self.ThreadsBox.currentIndex()+1
        Command=[self.plugin.exeP2SH,bitcoin.int_to_hex(ThreadsN-1),bitcoin.rev_hex(bitcoin.int_to_hex(NoncePos,2)),Pattern,Script] #2 Byte nonce position can handle large Script.
        if 'Windows' in platform.system(): self.processP2SH=subprocess.Popen(Command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,creationflags=0x8000000|0x4000)  #CREATE_NO_WINDOW|BELOW_NORMAL_PRIORITY_CLASS
        else: self.processP2SH=subprocess.Popen(Command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
        threading.Thread(target=self.communicateP2SH,args=[NoncePos*2,ThreadsN]).start()

        self.ButtonP2SH.clicked.disconnect()
        self.ButtonP2SH.clicked.connect(self.processP2SH.terminate)
        self.ButtonP2SH.setText('.terminate')
    def communicateP2SH(self,HexPos,ThreadsN):
        Time=time.time()    #I've verified there's no time delay from starting this thread.
        Script=self.processP2SH.communicate()[0].decode()
        Time=time.time()-Time

        self.ButtonP2SH.clicked.disconnect()
        self.ButtonP2SH.clicked.connect(self.clickedP2SH)
        self.ButtonP2SH.setText(self.ButtonTextP2SH)

        if not Script: return   #.terminate()
        Address=electroncash.address.Address.from_multisig_script(bitcoin.bfh(Script)).to_ui_string()
        if self.notify.isChecked():
            window=self.window
            window.notify(Address), window.activateWindow()
        self.AddContactVerify(Script)
        self.HashRate(Script[HexPos:HexPos+16],ThreadsN,Time)
        self.TTS(Address)
    def show_message(self):
        self.window.show_message(self.HiddenBoxP2SH.toPlainText())
        self.SearchContacts()  #A mysterious bug on Linux is fixed by only ever using the *primary* thread to .SearchContacts().
    def ScriptGen(self):
        for Word in self.Converter.text().split():   #Loop over inputs until a good address is found.
            try:
                Address=electroncash.address.Address.from_string(Word)
                PubKey=self.window.wallet.get_public_key(Address)   #If multisig address, return nothing since that'd require "get_public_keys" (not supported)
            except: continue
            try:    script=bitcoin.push_script(PubKey)+'ac7777'    #'77'=OP_NIP This line applies to standard wallet addresses. Output begins with '21'.
            except: script=       PubKey.to_script_hex()+'7777'    #Imported private key/s wallet. PubKey isn't a string, but an object of length 1, whose script already has 'ac'=OP_CHECKSIG at the end. Output begins with either 21 or 41.
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
            window.wallet.contacts.add(electroncash.contacts.Contact(Script+' VANITYTXID SCRIPT FROM '+P2PKHaddress.to_ui_string(),P2SHaddress,'address'),unique=True)
            window.update_wallet()    #Refresh GUI Contacts
        self.HiddenBoxP2SH.setPlainText(P2SHaddress+'\nAbove is the Address for the script (hex) below:\n'+Script+'\nAddress & Script have now been saved as a Contact in Wallet Contacts, if they belong to this wallet & have VanityTXID form.\nAfter sending the address a coin, import it into a watching-only wallet & use the Send→Preview button to obtain the TX hex needed for VanityTXID.')
    def HashRate(self,Nonce,ThreadsN,Time):
        Nonces=1+int(Nonce[2:],16)+int(int(Nonce[:2],16)/ThreadsN)*256**7  #The number of nonces the winning thread got through. First byte increases by ThreadsN whenever it has to.
        self.RateLabel.setText(_(str(round(Nonces/1e6/Time*ThreadsN,5))+' MH/s · '+str(round(Time,3))+' s'))
    def TTS(self,Text):
        if not self.TTSbox.isChecked(): return
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
                except: self.TTSbox.setChecked(False)
