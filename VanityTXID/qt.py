from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPlainTextEdit, QPushButton
from electroncash.i18n import _
from electroncash.plugins import BasePlugin, hook
import electroncash, subprocess, multiprocessing, threading, zipfile, shutil
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
        shutil.rmtree(self.parent.get_external_plugin_dir()+'\\VanityTXID')
    @hook
    def init_qt(self, qt_gui):
        """Hook called when a plugin is loaded (or enabled)."""
        # We get this multiple times.  Only handle it once, if unhandled.
        if len(self.wallet_windows):
            return
        Dir=self.parent.get_external_plugin_dir()
        Zip=zipfile.ZipFile(Dir+'\\VanityTXID-Plugin.zip')
        for Item in Zip.namelist(): 
            if 'bin' in Item: Zip.extract(Item,Dir+'\\VanityTXID')
        Zip.close()
        # These are per-wallet windows.
        for window in qt_gui.windows:
            self.load_wallet(window.wallet, window)
    @hook
    def load_wallet(self, wallet, window):
        """Hook called when a wallet is loaded and a window opened for it."""
        wallet_name = wallet.basename()
        self.wallet_windows[wallet_name] = window
        l = Ui(window, self)
        tab = window.create_list_tab(l)
        self.wallet_payment_tabs[wallet_name] = tab
        self.wallet_payment_lists[wallet_name] = l
        window.tabs.addTab(tab, QIcon(self.parent.get_external_plugin_dir()+"\\VanityTXID\\bin\\Icon.ico"), 'VanityTXID')
    @hook
    def close_wallet(self, wallet):
        subprocess.Popen('TaskKill /IM VanityTXID-Plugin.exe /F',creationflags=subprocess.CREATE_NO_WINDOW)
        wallet_name = wallet.basename()
        window = self.wallet_windows[wallet_name]
        del self.wallet_windows[wallet_name]
        wallet_tab = self.wallet_payment_tabs.get(wallet_name, None)
        if wallet_tab is not None:
            del self.wallet_payment_lists[wallet_name]
            del self.wallet_payment_tabs[wallet_name]
            i = window.tabs.indexOf(wallet_tab)
            window.tabs.removeTab(i)
class Ui(QDialog):
    def __init__(self, window, plugin):
        QDialog.__init__(self, window)
        self.window=window
        self.plugin=plugin

        VBox = QVBoxLayout()
        self.setLayout(VBox)
        
        Title=QLabel('VanityTXID v1.0.3');
        Title.setAlignment(Qt.AlignCenter)
        VBox.addWidget(Title)

        AddressesLabel=QLabel(_('VanityTXID Addresses: '))
        ConverterLabel=QLabel(_('Address converter: '))
        AddressesLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ConverterLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        VBoxAddressesLabels=QVBoxLayout()
        VBoxAddressesLabels.addWidget(AddressesLabel)
        VBoxAddressesLabels.addWidget(ConverterLabel)
        
        wallet = window.wallet
        self.AddressLine=QLineEdit()
        self.AddressLine.setReadOnly(True)
        self.FindAddresses()

        self.Converter=QLineEdit()
        self.Converter.setPlaceholderText(_('Paste standard BCH address here to convert it to P2SH, enabling sigscript malleability. Afterward the P2SH address will appear as a label in the Addresses tab. After sending it a coin, import it into a watching-only wallet.'))
        self.Converter.textEdited.connect(self.AddressGen)
        
        VBoxAddresses=QVBoxLayout()
        VBoxAddresses.addWidget(self.AddressLine)
        VBoxAddresses.addWidget(self.Converter)
        
        HBox=QHBoxLayout()
        HBox.addLayout(VBoxAddressesLabels)
        HBox.addLayout(VBoxAddresses)
        VBox.addLayout(HBox)
       
        self.TXBox = QPlainTextEdit()
        self.TXBox.setPlaceholderText(_('Paste raw TX hex here for all its VanityTXID inputs to be signed by this wallet, wherever possible, and mined with the pattern below. Pattern, Message & #Threads can all be left blank, in which case the result can be mined on a separate PC. Remember to set a higher fee in the watching-only wallet preferences, like 1.2 sat/B.'))
        VBox.addWidget(self.TXBox)
        
        self.HiddenBox=QPlainTextEdit()
        self.HiddenBox.textChanged.connect(self.ShowTX) #Hidden textbox allows C++ binary to provide final TX, before broadcast.

        PatternLabel=QLabel(_('TXID Starting Pattern (hex): '))
        MessageLabel=QLabel(_('Sigscript Message (hex): '))
        ThreadsLabel=QLabel(_('# of CPU Threads (dec): '))
        PatternLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        MessageLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ThreadsLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        VBoxLabels=QVBoxLayout()
        VBoxLabels.addWidget(PatternLabel)
        VBoxLabels.addWidget(MessageLabel)
        VBoxLabels.addWidget(ThreadsLabel)
        
        VBoxConfig=QVBoxLayout()
        self.Pattern=QLineEdit('00000')
        self.Pattern.setMaxLength(32);
        self.Pattern.setPlaceholderText(_('Enter desired starting pattern for TXID here. Blank is OK.'))
        VBoxConfig.addWidget(self.Pattern)
        
        self.Message=QLineEdit('deadbeef')
        self.Pattern.setMaxLength(510); #255B limit.
        self.Message.setPlaceholderText(_('Enter hex message, to appear first in all the created sigscripts. Blank is OK. e.g. convert text->hex and enter hex here.'))
        VBoxConfig.addWidget(self.Message)
        
        self.Threads=QLineEdit(_(str(multiprocessing.cpu_count())))
        self.Threads.setMaxLength(3);
        self.Threads.setPlaceholderText(_('Enter # of threads. Default is cpu_count. Integer between 1 & 256.'))
        VBoxConfig.addWidget(self.Threads)
        
        HBoxConfig=QHBoxLayout()
        HBoxConfig.addLayout(VBoxLabels)
        HBoxConfig.addLayout(VBoxConfig)
        VBox.addLayout(HBoxConfig)

        self.Button = QPushButton(_('Sign and/or Mine'))
        self.Button.clicked.connect(self.Clicked)
        VBox.addWidget(self.Button)
        
    def Clicked(self):
        def IsHex(String):
            if String=='': return True
            try:
                eval('0x'+String)
                return True
            except: return False
        if not IsHex(self.Pattern.text()): return   #Valid Pattern hex?
        if not IsHex(self.Message.text()): return   #Valid Message hex?
        if len(self.Pattern.text())>0 and not (self.Threads.text().isnumeric() and 0<int(self.Threads.text())<=256): return #Need #Threads to generate starting pattern.
        
        if len(self.Message.text())%2: self.Message.insert('0')
        Message=self.Message.text()
        MessageSize=int(len(Message)/2)
        
        TX=electroncash.Transaction(self.TXBox.toPlainText())
        try: TX.inputs()[0] and TX.outputs()    #Valid hex in text box?
        except: return
        wallet=self.window.wallet
        window=self.window
        AllLabels=list(wallet.labels.values())
        Password=None
        for InputN in range(len(TX.inputs())):   # Sign all VanityTXID inputs, whenever possible.
            Input=TX.inputs()[InputN]
            if Input['signatures']!=[None]: continue
            Address=Input['address']
            try:    #Does input in either address form belong to wallet labels?
                try:    Index=AllLabels.index(Address.to_cashaddr())
                except: Index=AllLabels.index(Address.to_string(Address.FMT_LEGACY))
                finally:
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
                    if Password is None: return #User doesn't want to provide password.
                try: PrivKey=bitcoin.deserialize_privkey(wallet.export_private_key(qAddress,Password))[1]
                except: Password=None   #Bad Password.
            if wallet.is_schnorr_enabled(): Sig=electroncash.schnorr.sign(PrivKey,bitcoin.Hash(bitcoin.bfh(TX.serialize_preimage(InputN))))
            else: Sig=TX._ecdsa_sign(PrivKey,bitcoin.Hash(bitcoin.bfh(TX.serialize_preimage(InputN))))
            del(PrivKey)
            
            Input['scriptSig']=bitcoin.int_to_hex(MessageSize)+Message+'00'+bitcoin.int_to_hex(len(Sig)+1)+Sig.hex()+'41'+bitcoin.int_to_hex(int(len(script)/2))+script
            TX.inputs()[InputN]=Input
        del(Password)
        TX=electroncash.Transaction(TX.serialize())
        
        for Input in TX.inputs():
            if Input['signatures']==[None]: 
                window.show_transaction(TX) # More sigs needed, return.
                return     
        Pattern=' '+self.Pattern.text()
        if Pattern==' ':
            window.show_transaction(TX)     #Empty Pattern, return
            return
            
        for Input in TX.inputs():   # Determine nonce position. Finding 'ac7777' is a shortcut to a full script analysis of P2SH inputs, which just takes more code.
            if Input['type']=='unknown' and 'ac7777'==Input['scriptSig'][-6:]:
                SigScript=Input['scriptSig']
                MessageLen=2*int(SigScript[0:2],16)
                SigScript=SigScript[2+MessageLen:]
                NonceLen=2*int(SigScript[0:2],16)
                SigScript=SigScript[2+NonceLen:]
                Input['scriptSig']=bitcoin.int_to_hex(MessageSize)+Message+'080000000000000000'+SigScript
                break
        TX=electroncash.Transaction(TX.serialize())
        NoncePos=' '+bitcoin.rev_hex(bitcoin.int_to_hex(int(TX.raw.find(SigScript)/2)-8,2))

        Threads=' '+bitcoin.int_to_hex(int(self.Threads.text())-1)    #I figure ' 00' means 1 since highest index is specified to C++ binary.    
        Dir=self.plugin.parent.get_external_plugin_dir()
        Command='"'+Dir+'\\VanityTXID\\bin\\VanityTXID-Plugin.exe"'+Threads+NoncePos+Pattern+' '+TX.raw
        Process=subprocess.Popen(Command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        threading.Thread(target=self.Bin,args=(Process,len(TX.raw))).start()
        
        self.Button.setText('TaskKill')
        self.Button.clicked.disconnect()
        self.Button.clicked.connect(self.Cancel)
    def Bin(self,Process,lenTX):
        self.HiddenBox.setPlainText(str(Process.communicate()[0])[2:2+lenTX])
        self.Button.setText('Sign and/or Mine')
        self.Button.clicked.disconnect()
        self.Button.clicked.connect(self.Clicked)
    def ShowTX(self):
        try: self.window.show_transaction(electroncash.Transaction(self.HiddenBox.toPlainText()))
        except: return
    def Cancel(self): subprocess.Popen('TaskKill /IM VanityTXID-Plugin.exe /F',creationflags=subprocess.CREATE_NO_WINDOW)
    def AddressGen(self):
        wallet=self.window.wallet
        for Word in self.Converter.text().split():   #Generate many addresses simultaneously.
            try:
                Address=electroncash.address.Address.from_string(Word)
                PubKey=wallet.get_public_key(Address)   #If multisig address return nothing since that'd require "get_public_keys" (not supported)
            except: continue
            P2SHAddress=Address.from_multisig_script(bitcoin.bfh(self.scriptCode(PubKey))).to_ui_string()
            wallet.labels[Address.to_string(Address.FMT_LEGACY)]=P2SHAddress
        wallet.save_labels()
        self.window.update_labels()
        self.FindAddresses()
    def scriptCode(self,PubKey): 
        Length=len(PubKey)
        if Length>1:return bitcoin.int_to_hex(int(Length/2))+PubKey+'ac7777'    #'77'=OP_NIP
        else:       return                     PubKey.to_script_hex()+'7777'    #Uncompressed PubKey is an object of length 1, whose script already has 'ac'=OP_CHECKSIG at the end.
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
                if pAddress.to_cashaddr()==label or pAddress.to_string(pAddress.FMT_LEGACY)==label:
                    self.AddressLine.insert(label+' ')  #List all P2SH addresses.
            except: continue
        