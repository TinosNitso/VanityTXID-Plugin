from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
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
        self.ICO=Dir+'src/Icon.ico'
        if shutil.os.path.exists(Dir): Extract=False   #Only ever extract zip (i.e. install) once.
        else:
            Extract=True
            Zip=zipfile.ZipFile(Dir[:-1]+'-Plugin.zip') #shutil._unpack_zipfile is an alternative function, but it'd extract everything.
            Zip.extract('src/Icon.ico',Dir)
            Zip.extract('bin/LICENSE.txt',Dir)
        if 'Windows' in platform.system():
            if '64' in platform.machine(): binDir='bin/Windows/'
            else: binDir='bin/Windows-x86/'
            self.EXE=Dir+binDir+'VanityTXID-Plugin.exe'
            if Extract: {Zip.extract(Item,Dir) for Item in Zip.namelist() if Item.startswith(binDir)}
        else:
            if 'Darwin' in platform.system(): Item='bin/Darwin/VanityTXID-Plugin'
            else: Item='bin/Linux/VanityTXID-Plugin'
            self.EXE=Dir+Item
            if Extract:
                Zip.extract(Item,Dir)
                subprocess.Popen(['chmod','+x',self.EXE])
        if Extract: Zip.close()
    def on_close(self):
        """BasePlugin callback called when the wallet is disabled among other things."""
        for window in self.windows.values(): self.close_wallet(window.wallet)
        shutil.rmtree(self.parent.get_external_plugin_dir()+'/VanityTXID')
    @hook
    def init_qt(self, qt_gui):
        """Hook called when a plugin is loaded (or enabled)."""
        if self.UIs: return # We get this multiple times.  Only handle it once, if unhandled.
        for window in qt_gui.windows: self.load_wallet(window.wallet, window)           # These are per-wallet windows.
    @hook
    def load_wallet(self, wallet, window):
        """Hook called when a wallet is loaded and a window opened for it."""
        wallet_name = wallet.basename()
        self.windows[wallet_name] = window
        l = UI(window, self)
        tab = window.create_list_tab(l)
        self.tabs[wallet_name] = tab
        self.UIs[wallet_name] = l
        window.tabs.addTab(tab, QIcon(self.ICO), 'VanityTXID')
    @hook
    def close_wallet(self, wallet):
        wallet_name = wallet.basename()
        try: self.UIs[wallet_name].Process.terminate() #Can't assume successful .terminate or else there's a disable bug.
        except: pass
        window = self.windows[wallet_name]
        window.tabs.removeTab(window.tabs.indexOf(self.tabs.get(wallet_name)))
        del self.UIs[wallet_name], self.tabs[wallet_name]
class UI(QDialog):
    def __init__(self, window, plugin):
        QDialog.__init__(self, window)
        self.window=window
        self.plugin=plugin

        Title=QLabel('VanityTXID v1.4.0')
        Title.setStyleSheet('font-weight: bold')
        Title.setAlignment(Qt.AlignCenter)

        AddressesLabel=QLabel(_('VanityTXID Addresses: '))
        ConverterLabel=QLabel(_('Address Converter: '))
        VBoxAddressesLabels=QVBoxLayout()
        VBoxAddressesLabels.addWidget(AddressesLabel)
        VBoxAddressesLabels.addWidget(ConverterLabel)
        
        self.AddressLine=QLineEdit()
        self.AddressLine.setReadOnly(True)
        self.FindAddresses()

        self.Converter=QLineEdit()
        self.Converter.setPlaceholderText(_('Paste BCH addresses here to convert them to P2SH, enabling sigscript malleability. They are saved as address labels. After sending a coin, import them into a watching-only wallet.'))
        self.Converter.textEdited.connect(self.AddressGen)
        
        VBoxAddresses=QVBoxLayout()
        VBoxAddresses.addWidget(self.AddressLine)
        VBoxAddresses.addWidget(self.Converter)
        
        HBox=QHBoxLayout()
        HBox.addLayout(VBoxAddressesLabels)
        HBox.addLayout(VBoxAddresses)

        self.TXBox = QPlainTextEdit()
        self.TXBox.setPlaceholderText(_("Paste raw TX hex here for inputs to be signed by this wallet wherever possible. It's TXID is then mined for the starting pattern below. Pattern & Message can be left blank, in which case the result can be mined on a separate PC. Remember to set a higher fee in the watching-only wallet preferences, like 1.2 sat/B. The fee depends on message size."))

        self.TextHex=QComboBox()
        self.TextHex.addItems([_('(text)'),_('(hex)')])
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
        self.PatternLine.setMaxLength(32);  #With 8 Byte nonce, unlikely to get more than 16.
        self.PatternLine.setPlaceholderText(_('(Optional) Enter starting pattern for TXID.'))
        VBoxConfig.addWidget(self.PatternLine)
        
        self.Message=QLineEdit()
        self.Message.setPlaceholderText(_('(Optional) Enter message. It appears first in all the created sigscripts. 520 byte limit.'))
        self.MaxMessage=520 #Other languages like Chinese require a few bytes per character, which can cause a size error when attempting to broadcast.
        self.Message.setMaxLength(self.MaxMessage)
        VBoxConfig.addWidget(self.Message)
        
        HBoxConfig=QHBoxLayout()
        HBoxConfig.addLayout(VBoxType)
        HBoxConfig.addLayout(VBoxLabels)
        HBoxConfig.addLayout(VBoxConfig)

        self.Button = QPushButton(_('Sign and/or Mine'))
        self.Button.clicked.connect(self.Clicked)
        
        self.TTSLen=QComboBox()
        self.TTSLen.addItems('Pronounce '+str(Len) for Len in range(1,65))
        self.TTSLen.setCurrentIndex(15)
        
        self.TTSRate=QComboBox()
        self.TTSRate.addItems('@ Rate '+str(Rate) for Rate in range(11))
        self.TTSRate.setCurrentIndex(5)
        
        self.ThreadsBox=QComboBox()
        self.ThreadsBox.addItems(str(N)+' Threads' for N in range(1,257))
        self.ThreadsBox.setCurrentIndex(shutil.os.cpu_count()-1)
        
        self.TTS=QCheckBox(_('TXID To Sound'))
        self.TTS.setChecked(True)
        self.TTS.toggled.connect(self.Toggled)
        self.l337=QCheckBox('1337')
        self.ActivateWindow=QCheckBox('.activateWindow')
        self.Notify=QCheckBox('.notify')
        self.HashRate=QLabel(_('_.__ MH/s'))

        HBoxOptions=QHBoxLayout()
        {HBoxOptions.addWidget(Widget) for Widget in [self.TTS,self.TTSLen,self.TTSRate,self.l337,self.ActivateWindow,self.Notify,self.ThreadsBox,self.HashRate]}
        {Label.setAlignment(Qt.AlignRight | Qt.AlignVCenter) for Label in [AddressesLabel,ConverterLabel,PatternLabel,MessageLabel]}
        
        VBox = QVBoxLayout()
        VBox.addWidget(Title)
        VBox.addLayout(HBox)
        VBox.addWidget(self.TXBox)
        VBox.addLayout(HBoxConfig)
        VBox.addWidget(self.Button)
        VBox.addLayout(HBoxOptions)
        self.setLayout(VBox)
        
        self.HiddenBox=QPlainTextEdit()
        self.HiddenBox.textChanged.connect(self.ShowTX) #Hidden textbox allows primary Qt thread to show_transaction.
    def Clicked(self):
        if self.TextHex.currentText()==_('(text)'): Message=binascii.hexlify(self.Message.text().encode()).decode()
        else:
            if not all([Char in '0123456789abcdefABCDEF' for Char in self.Message.text()]): return   #Valid Message hex?
            if len(self.Message.text())%2: self.Message.insert('0') #Add 0 if someone wants an odd hex Message.
            Message=self.Message.text()
        Message=Message[:self.MaxMessage*2]
        
        self.Pattern=self.PatternLine.text()
        if not all([Char in '0123456789abcdefABCDEF' for Char in self.Pattern]): return   #Valid Pattern hex?
        
        TX=electroncash.Transaction(self.TXBox.toPlainText())
        try: TX.inputs()[0] and TX.outputs()    #Valid hex in text box?
        except: return
        window=self.window
        wallet=window.wallet
        AllLabels=list(wallet.labels.values())
        Password=None
        for InputN in range(len(TX.inputs())):   # Sign all VanityTXID inputs, whenever possible.
            Input=TX.inputs()[InputN]
            if Input['signatures']!=[None]: continue    #Already signed.
            Address=Input['address']
            try:    #Does input in any address form belong to wallet labels?
                try:
                    try:    Index=AllLabels.index(Address.to_cashaddr())
                    except: Index=AllLabels.index(Address.to_string(Address.FMT_LEGACY))
                except:     Index=AllLabels.index(Address.to_slpaddr())
                qAddress=Address.from_string(list(wallet.labels)[Index])
                PubKey=wallet.get_public_key(qAddress)
            except: continue

            Input['type']='unknown'
            script=self.scriptCode(PubKey)
            Input['scriptCode']=script
            
            PrivKey=None
            if not wallet.has_password(): PrivKey=bytearray(bitcoin.deserialize_privkey(wallet.export_private_key(qAddress,None))[1])
            while PrivKey is None:  #Need loop to get the right password.
                if not Password:
                    try: Password=bytearray(window.password_dialog().encode())    #A bytearray is mutable, and may be easier to erase (more secure) than an immutable str.
                    except: return #User cancelled, since None can't be encoded.
                try: PrivKey=bytearray(bitcoin.deserialize_privkey(wallet.export_private_key(qAddress,Password.decode()))[1])
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
          
        if len(self.Pattern) is 0 or not TX.is_complete():
            window.show_transaction(TX)     #Empty Pattern or more sigs needed -> return.
            return
        for Input in TX.inputs():   # Determine nonce position. Finding 'ac7777' at the end is a shortcut to a full script analysis of P2SH inputs, which just takes more code.
            if Input['type']=='unknown' and Input['scriptSig'].endswith('ac7777'):
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
        except: return     #User is attempting to mine txn which can't be mined.
        
        ThreadsN=self.ThreadsBox.currentIndex()+1
        Threads=bitcoin.int_to_hex(ThreadsN-1)    #I figure '00' means 1 since highest thread index is specified to C++ binary.
        Command=[self.plugin.EXE,Threads,bitcoin.rev_hex(bitcoin.int_to_hex(NoncePos,3)),self.Pattern,TX.raw] #3 Byte nonce position.
        if 'Windows' in platform.system(): self.Process=subprocess.Popen(Command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,creationflags=0x8000000|0x4000)  #CREATE_NO_WINDOW|BELOW_NORMAL_PRIORITY_CLASS
        else: self.Process=subprocess.Popen(Command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
        threading.Thread(target=self.Bin,args=[len(TX.raw),NoncePos*2,ThreadsN]).start()

        self.Button.clicked.disconnect()
        self.Button.clicked.connect(self.Process.terminate)
        self.Button.setText('.terminate')
    def Bin(self,LenTX,HexPos,ThreadsN):
        Time=time.time()
        TX=str(self.Process.communicate()[0])[2:2+LenTX]
        Time2=time.time()

        self.Button.clicked.disconnect()
        self.Button.clicked.connect(self.Clicked)
        self.Button.setText('Sign and/or Mine')

        try: TXID=electroncash.Transaction(TX).txid_fast()
        except: return  #.terminate occurred.
        
        window=self.window
        if self.ActivateWindow.isChecked(): window.activateWindow()
        self.HiddenBox.setPlainText(TX)
        
        Nonces=1+int(TX[HexPos+2:HexPos+16],16)+int(int(TX[HexPos:HexPos+2],16)/ThreadsN)*256**7  #The number of nonces the winning thread got through. First byte increases by ThreadsN whenever it has to.
        self.HashRate.setText(_(str(round(Nonces/1e6/(Time2-Time)*ThreadsN,2))+' MH/s'))
        
        if self.Notify.isChecked(): window.notify(TXID)
        if self.TTS.isChecked():
            Text=TXID[:self.TTSLen.currentIndex()+1]
            if self.l337.isChecked(): Text=Text.translate(dict(zip(map(ord,'0123456789'),'OlZEASGTBP')))
            if 'Windows' in platform.system(): subprocess.Popen(['PowerShell','-C',"$V=New-Object -C SAPI.SPVoice;$V.Rate="+str(self.TTSRate.currentIndex())+";$V.Voice=$V.GetVoices().Item("+str(random.getrandbits(1))+");$V.Speak('"+Text+"')"],creationflags=0x8000000)  #Use slow PowerShell because MSHTA isn't allowed on 32-bit WIN10 Home N.
            else:
                WPM=str(round(175*(450/175)**(self.TTSRate.currentIndex()/10)))   #Compute non-linear Words-Per-Minute on POSix. 175->450 WPM. 450WPM max is specified by espeak.
                if 'Darwin' in platform.system():
                    Voices='Rishi Veena Moira Fiona Tessa Daniel Samantha Victoria Alex Fred'   #English only.
                    #Voices='Ting-Ting Sin-Ji'  #macOS users can pick a specific language here, e.g. Chinese.
                    #Voices='Daniel Alex Fred Samantha Victoria Tessa Fiona Karen Maged Ting-Ting Sin-Ji Mei-Jia Zuzana Sara Ellen Xander Rishi Veena Moira Satu Amelie Thomas Anna Melina Mariska Damayanti Alice Luca Kyoko Yuna Nora Zosia Luciana Joana Ioana Milena Yuri Laura Diego Paulina Juan Jorge Monica Alva Kanya Yelda'    #Uncomment this line to hear any language/accent.
                    subprocess.Popen(['say','-v',random.choice(Voices.split()),'-r',WPM,Text])
                else:
                    try: subprocess.Popen(['espeak','-s',WPM,'-p',str(random.choice(range(100))),Text]) # espeak required on Linux to hear TTS. sudo apt install espeak. Random -p pitch.
                    except: pass
    def ShowTX(self): self.window.show_transaction(electroncash.Transaction(self.HiddenBox.toPlainText()))
    def AddressGen(self):
        wallet=self.window.wallet
        for Word in self.Converter.text().split():   #Generate many addresses simultaneously.
            try:
                Address=electroncash.address.Address.from_string(Word)
                PubKey=wallet.get_public_key(Address)   #If multisig address, return nothing since that'd require "get_public_keys" (not supported)
            except: continue
            P2SHAddress=Address.from_multisig_script(bitcoin.bfh(self.scriptCode(PubKey))).to_ui_string()
            wallet.set_label(Address.to_string(Address.FMT_LEGACY),P2SHAddress)
        self.window.update_labels()
        self.FindAddresses()
    def scriptCode(self,PubKey):
        try:    return bitcoin.push_script(PubKey)+'ac7777'    #'77'=OP_NIP This line applies to standard wallet addresses. Output begins with '21'.
        except: return        PubKey.to_script_hex()+'7777'    #Imported private key/s wallet. PubKey isn't a string, but an object of length 1, whose script already has 'ac'=OP_CHECKSIG at the end. Output begins with either 21 or 41.
    def FindAddresses(self):
        wallet=self.window.wallet
        self.AddressLine.clear()
        for label in list(wallet.labels.values()):
            if not electroncash.address.Address.is_valid(label): continue
            Legacy=list(wallet.labels)[list(wallet.labels.values()).index(label)]   #Addresses in label memory use legacy format.
            try:
                qAddress=electroncash.address.Address.from_string(Legacy)
                PubKey=wallet.get_public_key(qAddress)
                pAddress=qAddress.from_multisig_script(bitcoin.bfh(self.scriptCode(PubKey)))
                if pAddress.to_cashaddr()==label or pAddress.to_string(pAddress.FMT_LEGACY)==label or pAddress.to_slpaddr()==label: #We can sign for all 3: CashAddr, Legacy & SLPAddr. The latter can throw an error which is fine.
                    self.AddressLine.insert(label+' ')  #List all P2SH addresses.
            except: continue
    def HexConverter(self):
        if self.TextHex.currentText()==_('(hex)'):
            self.Message.setMaxLength(self.MaxMessage*2)
            self.Message.setText(binascii.hexlify(self.Message.text().encode()).decode())
        else:
            try: self.Message.setText(bitcoin.bfh(self.Message.text()).decode())
            except: pass
            self.Message.setMaxLength(self.MaxMessage)
    def Toggled(self): {Box.setEnabled(self.TTS.isChecked()) for Box in [self.TTSLen,self.TTSRate,self.l337]}
    