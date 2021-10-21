from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPlainTextEdit, QPushButton, QCheckBox, QComboBox
from electroncash.i18n import _ #Language translator
from electroncash.plugins import BasePlugin, hook
import electroncash, subprocess, threading, zipfile, shutil, os, gc, random, binascii, time
from electroncash import bitcoin

class Plugin(BasePlugin):
    def __init__(self, parent, config, name):
        BasePlugin.__init__(self, parent, config, name)
        self.wallet_windows = {}
        self.wallet_payment_tabs = {}
        self.wallet_payment_lists = {}
    def on_close(self):
        """BasePlugin callback called when the wallet is disabled among other things."""
        for window in list(self.wallet_windows.values()): self.close_wallet(window.wallet)
        shutil.rmtree(self.parent.get_external_plugin_dir()+'/VanityTXID')
    @hook
    def init_qt(self, qt_gui):
        """Hook called when a plugin is loaded (or enabled)."""
        if len(self.wallet_windows): return # We get this multiple times.  Only handle it once, if unhandled.
        Dir=self.parent.get_external_plugin_dir()
        Zip=zipfile.ZipFile(Dir+'/VanityTXID-Plugin.zip')
        for Item in Zip.namelist(): 
            if 'bin' in Item: Zip.extract(Item,Dir+'/VanityTXID')
        Zip.close()
        if 'posix' in os.name:  #set executables executable for posix.
            Exec=Dir+'/VanityTXID/bin/VanityTXID-Plugin'
            if 'Darwin' in os.uname().sysname: Exec+='.app' #macOS seems to require we be specific.
            subprocess.Popen(['chmod','+x',Exec])
        for window in qt_gui.windows: self.load_wallet(window.wallet, window)           # These are per-wallet windows.
    @hook
    def load_wallet(self, wallet, window):
        """Hook called when a wallet is loaded and a window opened for it."""
        wallet_name = wallet.basename()
        self.wallet_windows[wallet_name] = window
        l = Ui(window, self)
        tab = window.create_list_tab(l)
        self.wallet_payment_tabs[wallet_name] = tab
        self.wallet_payment_lists[wallet_name] = l
        window.tabs.addTab(tab, QIcon(self.parent.get_external_plugin_dir()+"/VanityTXID/bin/Icon.ico"), 'VanityTXID')
        tab.update()    #I suspect this helps somehow - copied from the plugin template.
    @hook
    def close_wallet(self, wallet):
        wallet_name = wallet.basename()
        try: self.wallet_payment_lists[wallet_name].Process.terminate() #Can't assume successful termination or else there's a disable bug.
        except: pass
        window = self.wallet_windows[wallet_name]
        del self.wallet_windows[wallet_name]
        wallet_tab = self.wallet_payment_tabs.get(wallet_name, None)
        if wallet_tab is not None:
            del self.wallet_payment_lists[wallet_name]
            del self.wallet_payment_tabs[wallet_name]
            window.tabs.removeTab(window.tabs.indexOf(wallet_tab))
class Ui(QDialog):
    def __init__(self, window, plugin):
        QDialog.__init__(self, window)
        self.window=window
        self.plugin=plugin

        VBox = QVBoxLayout()
        self.setLayout(VBox)
        
        Title=QLabel('VanityTXID v1.3.2')
        Title.setStyleSheet('font-weight: bold')
        Title.setAlignment(Qt.AlignCenter)
        VBox.addWidget(Title)

        AddressesLabel=QLabel(_('VanityTXID Addresses: '))
        ConverterLabel=QLabel(_('Address Converter: '))
        AddressesLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ConverterLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
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
        VBox.addLayout(HBox)
       
        self.TXBox = QPlainTextEdit()
        self.TXBox.setPlaceholderText(_("Paste raw TX hex here for inputs to be signed by this wallet wherever possible. It's TXID is then mined for the starting pattern below. Pattern & Message can be left blank, in which case the result can be mined on a separate PC. Remember to set a higher fee in the watching-only wallet preferences, like 1.2 sat/B. The fee depends on message size."))
        VBox.addWidget(self.TXBox)
        
        self.HiddenBox=QPlainTextEdit()
        self.HiddenBox.textChanged.connect(self.ShowTX) #Hidden textbox allows C++ binary to provide final TX, before broadcast.

        self.TextHex=QComboBox()
        self.TextHex.addItems([_('(text)'),_('(hex)')])
        self.TextHex.activated.connect(self.HexConverter)
        VBoxType=QVBoxLayout()
        VBoxType.addWidget(QLabel(_('(hex)')))
        VBoxType.addWidget(self.TextHex)
        VBoxType.addWidget(QLabel(_('(dec)')))

        PatternLabel=QLabel(_('TXID Starting Pattern: '))
        MessageLabel=QLabel(_('Sigscript Message: '))
        ThreadsLabel=QLabel(_('# of CPU Threads: '))
        PatternLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        MessageLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ThreadsLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        VBoxLabels=QVBoxLayout()
        VBoxLabels.addWidget(PatternLabel)
        VBoxLabels.addWidget(MessageLabel)
        VBoxLabels.addWidget(ThreadsLabel)
        
        VBoxConfig=QVBoxLayout()
        self.PatternLine=QLineEdit('00000')
        self.PatternLine.setMaxLength(32);  #With 8 Byte nonce, unlikely to get more than 16.
        self.PatternLine.setPlaceholderText(_('(Optional) Enter starting pattern for TXID.'))
        VBoxConfig.addWidget(self.PatternLine)
        
        self.Message=QLineEdit()
        self.Message.setPlaceholderText(_('(Optional) Enter message. It appears first in all the created sigscripts. 512 byte limit.'))
        self.MaxMessage=512 #By trial and error 1023 didn't work, but 512 bytes did. I don't know the exact limit.
        self.Message.setMaxLength(self.MaxMessage)
        VBoxConfig.addWidget(self.Message)
        
        self.ThreadsBox=QComboBox()
        self.ThreadsBox.addItems(list(map(str,range(1,257))))
        self.ThreadsBox.setCurrentIndex(os.cpu_count()-1)
        
        self.TTS=QCheckBox(_('TXID To Sound'))
        self.TTS.setChecked(True)
        self.l337=QCheckBox('1337')
        self.l337.setChecked(True)
        self.ActivateWindow=QCheckBox('.activateWindow')
        self.ActivateWindow.setChecked(True)
        self.Notify=QCheckBox('.notify')
        self.HashRate=QLabel(_('_.__ MH/s'))

        HBoxCheck=QHBoxLayout()
        HBoxCheck.addWidget(self.ThreadsBox)
        HBoxCheck.addWidget(self.TTS)
        HBoxCheck.addWidget(self.l337)
        HBoxCheck.addWidget(self.ActivateWindow)
        HBoxCheck.addWidget(self.Notify)
        HBoxCheck.addWidget(self.HashRate)
        VBoxConfig.addLayout(HBoxCheck)
        
        HBoxConfig=QHBoxLayout()
        HBoxConfig.addLayout(VBoxType)
        HBoxConfig.addLayout(VBoxLabels)
        HBoxConfig.addLayout(VBoxConfig)
        VBox.addLayout(HBoxConfig)

        self.Button = QPushButton(_('Sign and/or Mine'))
        self.Button.clicked.connect(self.Clicked)
        VBox.addWidget(self.Button)

    def Clicked(self):
        if self.TextHex.currentText()==_('(text)'): Message=binascii.hexlify(self.Message.text().encode()).decode()
        else:
            if not all([Char in '0123456789abcdefABCDEF' for Char in self.Message.text()]): return   #Valid Message hex?
            if len(self.Message.text())%2: self.Message.insert('0') #Add 0 if someone wants an odd hex Message.
            Message=self.Message.text()
        self.Pattern=self.PatternLine.text()
        if not all([Char in '0123456789abcdefABCDEF' for Char in self.Pattern]): return   #Valid Pattern hex?
        
        TX=electroncash.Transaction(self.TXBox.toPlainText())
        try: TX.inputs()[0] and TX.outputs()    #Valid hex in text box?
        except: return
        wallet=self.window.wallet
        window=self.window
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
            while PrivKey is None:  #Need loop to get the right password.
                if wallet.has_password() and Password is None:
                    Password=window.password_dialog()
                    if Password is None: return #User cancelled.
                try: PrivKey=bitcoin.deserialize_privkey(wallet.export_private_key(qAddress,Password))[1]
                except: Password=None   #Bad Password.
            if wallet.is_schnorr_enabled(): Sig=electroncash.schnorr.sign(PrivKey,bitcoin.Hash(bitcoin.bfh(TX.serialize_preimage(InputN))))
            else: Sig=TX._ecdsa_sign(PrivKey,bitcoin.Hash(bitcoin.bfh(TX.serialize_preimage(InputN))))
            PrivKey='B'*52  #How to delete an immutable string of length up to 52 long? 
            del PrivKey
            
            Input['scriptSig']=bitcoin.push_script(Message)+'00'+bitcoin.int_to_hex(len(Sig)+1)+Sig.hex()+'41'+bitcoin.int_to_hex(int(len(script)/2))+script
        while wallet.can_sign(TX):  #Also sign using standard wallet. Need loop to get the right password. There's an issue where we fail to add a Message to nothing but a simple P2PKH input.
            TX.set_sign_schnorr(wallet.is_schnorr_enabled())
            if wallet.has_password() and Password is None:
                Password=window.password_dialog()
                if Password is None: return #User cancelled.
            try: wallet.sign_transaction(TX,Password)
            except: Password=None    #Bad Password
        Password='B'*52
        del Password 
        gc.collect()    #Garbage Collector for PrivKey & Password memory allocation.
        TX=electroncash.Transaction(TX.serialize())
          
        if len(self.Pattern) is 0 or not TX.is_complete():
            window.show_transaction(TX)     #Empty Pattern or more sigs needed -> return.
            return
        for Input in TX.inputs():   # Determine nonce position. Finding 'ac7777' at the end is a shortcut to a full script analysis of P2SH inputs, which just takes more code.
            if Input['type']=='unknown' and 'ac7777'==Input['scriptSig'][-6:]:
                SigScript=Input['scriptSig']
                MessageSize=int(SigScript[0:2],16)
                SigScript=SigScript[2:]
                if MessageSize==0x4c:   #OP_PUSHDATA1
                    MessageSize=int(SigScript[0:2],16)
                    SigScript=SigScript[2:]
                elif MessageSize==0x4d: #OP_PUSHDATA2
                    MessageSize=int(bitcoin.rev_hex(SigScript[0:4]),16)
                    SigScript=SigScript[4:]
                elif MessageSize==0x4e: #OP_PUSHDATA4   It's impossible to reach this size.
                    MessageSize=int(bitcoin.rev_hex(SigScript[0:8]),16)
                    SigScript=SigScript[8:]
                SigScript=SigScript[2*MessageSize:]
                NonceSize=int(SigScript[0:2],16)
                SigScript=SigScript[2+2*NonceSize:]
                Input['scriptSig']=bitcoin.push_script(Message)+'080000000000000000'+SigScript
                break
        TX=electroncash.Transaction(TX.serialize())
        try: self.NoncePos=int(TX.raw.find(SigScript)/2)-8
        except: return     #User is attempting to mine txn which can't be mined.
        
        self.ThreadsN=int(self.ThreadsBox.currentText())
        Threads=bitcoin.int_to_hex(self.ThreadsN-1)    #I figure ' 00' means 1 since highest index is specified to C++ binary.    
        Dir=self.plugin.parent.get_external_plugin_dir()
        Command=[Dir+'/VanityTXID/bin/VanityTXID-Plugin',Threads,bitcoin.rev_hex(bitcoin.int_to_hex(self.NoncePos,3)),self.Pattern,TX.raw] #3 Byte nonce position.
        if 'nt' in os.name:
            Command[0]+='.exe'
            self.Process=subprocess.Popen(Command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,creationflags=0x8000000|0x4000)  #CREATE_NO_WINDOW|BELOW_NORMAL_PRIORITY_CLASS
        else:
            if 'Darwin' in os.uname().sysname: Command[0]+='.app'
            self.Process=subprocess.Popen(Command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
        self.Time=time.time()
        threading.Thread(target=self.Bin,args=[len(TX.raw)]).start()
        
        self.Button.setText('.terminate')
        self.Button.clicked.disconnect()
        self.Button.clicked.connect(self.Process.terminate)
    def Bin(self,lenTX): self.HiddenBox.setPlainText(str(self.Process.communicate()[0])[2:2+lenTX])
    def ShowTX(self):
        TX=electroncash.Transaction(self.HiddenBox.toPlainText())
        try:
            HexPos=self.NoncePos*2+2    #Assume only 7/8 nonce bytes are being used by each thread.
            Nonce=int(TX.raw[HexPos:HexPos+14],16)
            self.HashRate.setText(_(str(round(Nonce/(time.time()-self.Time)/1e6*self.ThreadsN,2))+' MH/s')) #Calculate hashrate before notification.
            
            TXID=TX.txid_fast()
            if self.TTS.isChecked():    #TTS first due to bug where mshta captures focus within 60ms.
                Text=TXID[:len(self.Pattern)+4] #I like to hear a few digits after the pattern.
                if self.l337.isChecked(): Text=Text.translate({ord('0'):'O',ord('1'):'L',ord('3'):'E',ord('4'):'A',ord('5'):'S',ord('6'):'G',ord('7'):'T'})
                if 'nt' in os.name:
                    subprocess.Popen(["mshta","javascript:code(close((v=new ActiveXObject('SAPI.SpVoice'))&&(v.Voice=v.GetVoices().Item("+str(random.getrandbits(1))+"))&&v.Speak('"+Text+"')))"])
                    if self.ActivateWindow.isChecked(): time.sleep(0.06)    #Only delay for focus.
                elif 'Darwin' in os.uname().sysname : subprocess.Popen(['say',Text])
                else                                : subprocess.Popen(['espeak',Text]) # eSpeak required on Linux to hear TTS.
            window=self.window
            if self.ActivateWindow.isChecked(): window.activateWindow()
            window.show_transaction(TX)
            if self.Notify.isChecked(): window.notify(TXID)
        except: pass
        self.Button.setText('Sign and/or Mine')
        self.Button.clicked.disconnect()
        self.Button.clicked.connect(self.Clicked)
    def AddressGen(self):
        wallet=self.window.wallet
        for Word in self.Converter.text().split():   #Generate many addresses simultaneously.
            try:
                Address =electroncash.address.Address.from_string(Word)
                PubKey=wallet.get_public_key(Address)   #If multisig address return nothing since that'd require "get_public_keys" (not supported)
            except: continue
            P2SHAddress=Address.from_multisig_script(bitcoin.bfh(self.scriptCode(PubKey))).to_ui_string()
            wallet.set_label(Address.to_string(Address.FMT_LEGACY),P2SHAddress)
        self.window.update_labels()
        self.FindAddresses()
    def scriptCode(self,PubKey):
        if len(PubKey)>1:   return bitcoin.push_script(PubKey)+'ac7777'    #'77'=OP_NIP
        else:               return        PubKey.to_script_hex()+'7777'    #Uncompressed PubKey is an object of length 1, whose script already has 'ac'=OP_CHECKSIG at the end.
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
        