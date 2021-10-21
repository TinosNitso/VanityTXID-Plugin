# VanityTXID-Plugin

![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshot-v1.3.2.png)

Windows users can update their SLP Edition to the pre-release 3.6.7-dev6. It seems to have a bug-fix which makes VanityTXID work faster. I've checked the MH/s and the newer one is more consistent.

The screenshot for v1.3.2 involved nonce '0300000000361edc', which corresponds to the 4th thread, and only took about half a minute. I suspect assembly code may be four times faster than the 0.67 MH/s seen here. For my i7-2600 CPU, I've read estimates ranging from 5 to 24 MH/s for an 80B block header.

![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshot2.png)
![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshot-v1.1.0.png)

Generate txn IDs starting with a specific pattern, using a standard wallet + plugin & watching-only wallet. Available for Electron Cash (incl. SLP Edition) on Windows, Linux & macOS. Written in Python, & C++ for the miner. To install the latest version download "VanityTXID-Plugin.zip" above, or from the proper release. Using this plugin users can create and send SLP tokens with custom token/txn ID, like this PoW NFT (minted in about 30secs): https://simpleledger.info/token/00000002dad1d1f7e12cb4fc6239a1223ed29470a909a8e8078ee51f1b5ae3a9

v1.3.2 SHA256 Checksum: 8472560065d06c0159cf3c602426073e4817586431bfa7a7652036c2bc9252e4

A fundamental issue is that 0-conf doesn't apply to the TXID itself. The payment amount can't be changed, but the TXID & message can change before confirmation. If it ever fails, the smart contract can be improved. A 0-conf message could be signed for using OP_CHECKDATASIG - the smart contract is just more complicated.

main.cpp & Icon.rc are compiled together using -O3 -s with the gcc compiler. The three .dll libraries are extracted directly from 'codeblocks-20.03-32bit-mingw-32bit-nosetup.zip'. Linux & macOS compiling don't use Icon.rc. I've now included the Windows project file with example arguments so others can build & run immediately. There's a serious issue when it comes to deterministic builds which are verifiably identical to the source code.

v1.3.2 notes:
- Approximate hash rate in MH/s. It assumes all threads are equal, the nonce doesn't make it to the 8th byte, & it's not reliable if there are too many threads. 1.4 MH/s is a good rate for me, for 197B.
- 1337 option for TTS.
- Bugfix: Message size exactly 78 bytes now always works.
- .activateWindow may help if someone's watching a video. Fixes an issue where Windows mshta steals focus for the javascript TTS. It involves a 60ms lag, to recapture focus.
- Slightly improved placeholder text.
- To update, users should close & re-open their wallet, due to some reinstallation bug.

v1.3.1 Notes:
- Max message size now 512 Bytes instead of 75B. e.g. https://blockchain.com/bch/tx/00000073d648302417ad306912c4a43ea1aa91907921d13d95844f58637329c0
- Optional Notifications. User can change their mind after mining begins.
- Optional TTS on every OS! I've set it to pronounce the pattern + 4 extra digits. Linux requires eSpeak or else there's no voice (sudo apt install espeak). eSpeak comes with Ubuntu. In the future I might add a speed setting, and conceivably l33t (pronounce 0 as O etc). 
- Message input in either hex or text. Works as a hex converter! It even works with Chinese.
- Removed/improved IsHex() method.
- Bold heading, altered placeholder text.

v1.3.0 Notes:
- Full SLP Edition support! That means VanityTXID addresses can now take SLPAddr format. We could already mint vanity token IDs by using a watching-only wallet in the SLP edition, but now the plugin works natively in the SLP Edition. I've tested both Windows & Linux, and will try to update to at least macOS Catalina tomorrow. One zip for all editions & OSs.
- multiprocessing module wasn't required for os.cpu_count(). No change to binaries (C++).

v1.2.1 notes:
- Bug fix for disable &/or uninstall error. To uninstall v1.2.0 users need to close and then re-open the wallet.
- Bug fix when user attempts to mine a txn which can't be mined.
- Will now sign both P2SH & P2PKH, in any order, wherever possible. They can be combined using the watching-only wallet, along with other inputs which are signed separately.
- I've changed the binaries to use a 3 Byte nonce position, exit() function and more constants.

v1.2.0 notes:
- Full support for macOS, version High Sierra and newer.
- Bug fixed where closing irrelevant wallets cancels mining. Simplified Python code.
- Password & PrivKey are now overwritten before being deleted, and then Garbage Collected.
- C++ code simplified by using const nonce position.
- All C++ warnings resolved.
- New license file mentions copied plugin template code. github.com/KarolTrzeszczkowski/Electron-Cash-Plugin-Template

v1.1.0 notes:
- Linux now supported. Linux binary is about 17% faster. I dunno why.
- Downgraded Windows binary to 32 bit from 64 bit, since EC is only 32 bit on Windows.
- Simplified C++ using exit(0).

v1.0.3 notes:
- We can now instantly convert any number of addresses by first selecting them in the Addresses tab and then copy-paste all of them over to the Address Converter in VanityTXID.
- Now have a complete list of P2SH addresses, which is updated whenever user does anything to the Converter box. These are guaranteed to be correct, unlike random labels in the Addresses tab.
- I fixed an error from v1.0.2 where the user types in a wrong password. Now it asks again, and if user hits cancel then we return to normal. I simplified a lot of Python script, but no change to binary.

v1.0.2 notes:
- Nonce position can now be up to 256**2, so the input being "mined" doesn't have to be the first. (There was also a bug in the C++ binary of v1.0.1) e.g. now in www.blockchain.com/bch/tx/0000006727815232d1fd48e1988b9aea8b3e4cd060dfbe44c4a52239c71b5cd5 'deadbeef' doesn't appear until the 2nd input.
- Improved code so that raw TX hex can be repeatedly mined (copy-paste after mining, and then again etc).
- Full support for legacy P2SH form (starting with '3' instead of 'p').
- Multiple P2SH address display, but generating lots of addresses at once will be in next update.
- Added version title.

v1.0.1 notes:
- Now support uncompressed keys. e.g. www.blockchain.com/bch/tx/000000821afbda9e137ab90bf5de3cad8bf8a3bbe218b7f9c26566ec5779fd8f
- Have improved UI with labels.
- Have fixed many error reports by using try:/except: functions. I had crash reporter disabled so didn't realize there were errors.
- Found Python bitcoin.int_to_hex
- del(Password) after it's used.
- 128<Thread#<256 now allowed (was bug in C++ code). I've found 256 threads might be a tiny bit faster than 8 for patterns six long.

