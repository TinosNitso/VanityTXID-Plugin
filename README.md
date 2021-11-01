# VanityTXID-Plugin

![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshot-v1.3.2.png)

v1.3.2 screenshot used nonce '0300000000361edc', which corresponds to the 4th thread, and only took about half a minute. I suspect assembly code may be four times faster than the 0.67 MH/s seen here. For my i7-2600 CPU, I've read estimates ranging from 5 to 24 MH/s for an 80B block header. For 197B I get just over 1.9 MH/s (v1.4.0 uses BCHN sha256.cpp).

SLP Edition version 3.6.7-dev6 doesn't use up a CPU processor in the background, unlike 3.6.6. It also has newer code. The issue arises on all 3 OSs.

![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshot2.png)

![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshot-v1.3.3.png)

Generate txn IDs starting with a specific pattern, using a standard wallet + plugin & watching-only wallet. Available for Electron Cash (incl. SLP Edition) on Windows, Linux & macOS. Written in Python, & C++ for the miner. To install the latest version download "VanityTXID-Plugin.zip" above, or from the proper release. Using this plugin users can create and send SLP tokens with custom token/txn ID, like this PoW NFT (minted in about 30secs): https://simpleledger.info/token/00000002dad1d1f7e12cb4fc6239a1223ed29470a909a8e8078ee51f1b5ae3a9

A fundamental issue is that 0-conf doesn't apply to the TXID itself. The payment amount can't be changed, but the TXID & message can change before confirmation. If it ever fails, the contract can be improved. A 0-conf message could be signed for using OP_CHECKDATASIG - the smart contract is just more complicated.

main.cpp & Icon.rc are compiled together using -O3 -s -march=corei7 g++.exe compiler flags. All .dll libraries are extracted from 'codeblocks-20.03mingw-nosetup.zip' & 'codeblocks-20.03-32bit-mingw-32bit-nosetup.zip'. Linux compiling doesn't use Icon.rc, and requires linking pthread library in Code::Blocks ('sudo apt install codeblocks'). In macOS don't use Code::Blocks, instead enter 'g++ -std=c++11 -O3 ./main.cpp' into terminal. macOS will download & install g++ if needed. Then rename the resulting 'A.out' to 'VanityTXID-Plugin' and it's ready to go inside the zip if you want to check your own build's hash rate.

A Windows project file with example arguments is included, so others can build & run immediately (I just broadcast the payment so no one else can). There's a serious issue when it comes to deterministic builds which are verifiably identical to the source code. Instead of the checksums, which keep changing every time I build, it's better to look at the exact number of bytes, e.g. 88,576 bytes. It should be possible to reproduce each build's exact size.

Linux requires eSpeak for TXID To Sound (enter 'sudo apt install espeak' in terminal). Linux in VirtualBox (screenshot) is probably only half the speed it was in Windows' own Hyper-V, but that one doesn't support macOS.

v1.4.0: SHA256 Checksum: cd254b21f771353738d80306f4f9648e8ef60d9e93b118b7786d20bd46c11693
- ~31% speed increase by using Bitcoin Core's CSHA256 C++ code. Binary sizes are all much larger now. I've removed the zedwood license. In a future update I might bring it back as a UI selection, since zedwood probably wins on simplicity (imagine having to write every line yourself). Users might want to select between CryptoPP, OpenSSL, Bitcoin Core & zedwood, to check the hash rates. I've noticed results which are a bit too impressive inside Linux & macOS VMs. eg I got 1.4 MH/s using only 4 Threads in a very slow macOS Catalina VirtualBox. This should mean I get more than 1.9 MH/s natively in Windows. I'll probably try a native Linux test. It could be there's an issue with MinGW being slow (poor Windows build).
- BugFix: Windows TTS now uses PowerShell -C instead of MSHTA (MicroSoft HTml App.) since the latter isn't allowed on 32-bit WIN10 Home N.
- Improved Python script. Only ever extract binaries from zip once, on enable (faster startup). Disabling plugin still removes all binaries.
- BugFix: Hash rate was always over by ~1% (3*1/255) due to 'for' loops failing to catch a few used nonce bytes at #255 (or -1). I was just about to switch back from the new 'do' loops, due to them being 1% slower!
- Random espeak pitch now in Linux, which is the synth version of random voice. BugFix: Lack of espeak no longer throws an error.
- WPM (POSix) now exponential against Rate index. Default @ Rate 5. Max WPM reduced to 450.
- There's still a bug when a plugin changes version number (wallet must restart to finish update). Language Translator not working (module can only handle one word at a time).

v1.3.4:
- Windows 64 bit binary (with i7-AVX tuning) slightly faster on my CPU (1.5 MH/s instead of 1.4 MH/s). Back in v1.1.0 I downgraded to 32-bit, before I could check the MH/s. Just because EC is 32-bit, doesn't mean its plugins should always be! TBH I haven't tested a 32-bit VM yet. The plugin has now doubled in size. I haven't rebuilt the posix binaries.
- Message size limit increaed to 520 Bytes, instead of 512B. Technically for data a better scriptcode could involve 3 OP_NIPs (777777) at the end, since it takes a few to max out the scriptsig limit (1650B). 1650B may correspond to something like a 15-of-15 multisig input, or a few OP_NIPs. 3 OP_NIPs, instead of 2, may be a bit like signing with a middle name, as well as first and last names. 77777777 may be even better (2 middle names), due to an added nonce being separate, for a vanity TXID. 520B example: https://blockchain.com/bch/tx/00000003ace42ee6d165eb3b37d27b42703cb0a56ce2990c60a84e01e78ae6d7
- 1337 off by default, now dict uses 'OlZEASGTBP'.
- Unchecking TTS now disables TTS controls, etc.
- Simpler Python script.

v1.3.3:
- PrivKey & Password now mutable bytearrays instead of immutable strings.
- User can now set how many TXID digits to pronounce, as well as TTS Rate. On POSIX 1->10 corresponds to 175->720 WPM. In a future version I might enable slower speeds, since that could help with 1337.
- Random voice in macOS, chosen from 10! I tested in Catalina. To hear hex/1337 speak in any language or accent, a macOS user can uncomment the long Voices line in qt.py
- More elegant HashRate timing, & formula which handles all 8B of nonce. More elegant script.

v1.3.2:
- Approximate hash rate in MH/s. It assumes all threads are equal, the nonce doesn't make it to the 8th byte, & it's not reliable if there are too many threads. 1.4 MH/s is a good rate for me, for 197B.
- 1337 option for TTS.
- Bugfix: Message size exactly 78 bytes now always works.
- .activateWindow may help if someone's watching a video. Fixes an issue where Windows mshta steals focus for the javascript TTS. It involves a 60ms lag, to recapture focus.

v1.3.1:
- Max message size now 512 Bytes instead of 75B. e.g. https://blockchain.com/bch/tx/00000073d648302417ad306912c4a43ea1aa91907921d13d95844f58637329c0
- Optional Notifications. User can change their mind after mining begins.
- Optional TTS on every OS! I've set it to pronounce the pattern + 4 extra digits. Linux requires eSpeak or else there's no voice (sudo apt install espeak). eSpeak comes with Ubuntu. In the future I might add a speed setting, and conceivably l33t (pronounce 0 as O etc). 
- Message input in either hex or text. Works as a hex converter! It even works with Chinese.
- Removed/improved IsHex() method.
- Bold heading, altered placeholder text.

v1.3.0:
- Full SLP Edition support! That means VanityTXID addresses can now take SLPAddr format. We could already mint vanity token IDs by using a watching-only wallet in the SLP edition, but now the plugin works natively in the SLP Edition. I've tested both Windows & Linux, and will try to update to at least macOS Catalina tomorrow. One zip for all editions & OSs.
- multiprocessing module wasn't required for os.cpu_count(). No change to binaries (C++).

v1.2.1:
- Bug fix for disable &/or uninstall error. To uninstall v1.2.0 users need to close and then re-open the wallet.
- Bug fix when user attempts to mine a txn which can't be mined.
- Will now sign both P2SH & P2PKH, in any order, wherever possible. They can be combined using the watching-only wallet, along with other inputs which are signed separately.
- I've changed the binaries to use a 3 Byte nonce position, exit() function and more constants.

v1.2.0:
- Full support for macOS, version High Sierra and newer.
- Bug fixed where closing irrelevant wallets cancels mining. Simplified Python code.
- Password & PrivKey are now overwritten before being deleted, and then Garbage Collected.
- C++ code simplified by using const nonce position.
- All C++ warnings resolved.
- New license file mentions copied plugin template code. github.com/KarolTrzeszczkowski/Electron-Cash-Plugin-Template

v1.1.0:
- Linux now supported. Linux binary is about 17% faster. I dunno why.
- Downgraded Windows binary to 32 bit from 64 bit, since EC is only 32 bit on Windows.
- Simplified C++ using exit(0).

v1.0.3:
- We can now instantly convert any number of addresses by first selecting them in the Addresses tab and then copy-paste all of them over to the Address Converter in VanityTXID.
- Now have a complete list of P2SH addresses, which is updated whenever user does anything to the Converter box. These are guaranteed to be correct, unlike random labels in the Addresses tab.
- I fixed an error from v1.0.2 where the user types in a wrong password. Now it asks again, and if user hits cancel then we return to normal. I simplified a lot of Python script, but no change to binary.

v1.0.2:
- Nonce position can now be up to 256**2, so the input being "mined" doesn't have to be the first. (There was also a bug in the C++ binary of v1.0.1) e.g. now in www.blockchain.com/bch/tx/0000006727815232d1fd48e1988b9aea8b3e4cd060dfbe44c4a52239c71b5cd5 'deadbeef' doesn't appear until the 2nd input.
- Improved code so that raw TX hex can be repeatedly mined (copy-paste after mining, and then again etc).
- Full support for legacy P2SH form (starting with '3' instead of 'p').
- Multiple P2SH address display, but generating lots of addresses at once will be in next update.
- Added version title.

v1.0.1:
- Now support uncompressed keys. e.g. www.blockchain.com/bch/tx/000000821afbda9e137ab90bf5de3cad8bf8a3bbe218b7f9c26566ec5779fd8f
- Have improved UI with labels.
- Have fixed many error reports by using try:/except: functions. I had crash reporter disabled so didn't realize there were errors.
- Found Python bitcoin.int_to_hex
- del(Password) after it's used.
- 128<Thread#<256 now allowed (was bug in C++ code). I've found 256 threads might be a tiny bit faster than 8 for patterns six long.

