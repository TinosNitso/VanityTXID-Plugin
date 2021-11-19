# VanityTXID-Plugin
 
Next version, 1.6.0, will include a third app, **VanityHash**, to vanitize any file's SHA256 Checksum, by appending an 8B nonce. These document hashes are fundamental to various protocols. VanityTXID-Plugin.zip Checksum should start with a few zeros (under 30secs to generate for 1.3MiB). I like putting powerful apps all inside a Bitcoin wallet. I'll re-build the VanityTXID-Plugin exe since the winning thread is missing 'goto Finish' & accidentally does an extra hash at the end (tiny speed issue due to code Copy-Paste missing a line).
 
![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshots/v1.5.0.png)

v1.5.0 screenshot used nonce '07000000006e2b40', corresponding to the 8th thread. with hash rate 1.2 MH/s for 394B txn. I suspect assembly code might be a few times faster than sha256.cpp (BCHN). For my i7-2600 CPU, I've read estimates ranging from 5 to 24 MH/s for an 80B block header. For 197B I get nearly 2 MH/s, & 6.2 MH/s is for address generation (quadruple the speed of VanitygenCash).

SLP Edition versions 3.6.7-dev6 & 3.6.7-dev5 (for macOS) don't use up a CPU processor in the background, unlike 3.6.6. The pre-releases also have newer code. The CPU usage issue arises on all 3 OSs. As of v1.5.0 I've dropped support for 3.6.6 due to the difference in how Wallet Contacts are handled.

![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshots/Screenshot-v1.4.1.png)

![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshots/v1.5.1.png)

Generate txn IDs starting with a specific pattern, using a standard wallet + plugin & watching-only wallet. Also generate vanity addresses, as well as vanity addresses for any Script (smart contract). Available for Electron Cash (incl. SLP Edition) on Windows, Linux & macOS. Written in Python, & C++ for the miner. To install the latest version download "VanityTXID-Plugin.zip" above, or from the proper release. Using this plugin users can create and send SLP tokens with custom token/txn ID, like this PoW NFT (minted in about 30secs): https://simpleledger.info/token/00000002dad1d1f7e12cb4fc6239a1223ed29470a909a8e8078ee51f1b5ae3a9

A fundamental issue is that 0-conf doesn't apply to the TXID itself. The payment amount can't be changed, but the TXID & message can change before confirmation. If it ever fails, the contract can be improved, or else mining pools can mine the vanity TXID directly in return for a confidential fee. eg a new version can include simple nonce checksum/s, s.t. miners can't easily deduce a vanity contract is being used. A "smarter" contract could also sign 0-conf message using OP_CHECKDATASIG.

VanityTXID.cpp & VanityTXID.rc are compiled together using -O3 -s -march=corei7 g++.exe compiler flags. Same for VanityP2SH. All .dll libraries are extracted from 'codeblocks-20.03mingw-nosetup.zip' & 'codeblocks-20.03-32bit-mingw-32bit-nosetup.zip'. Linux compiling doesn't use Icon.rc, and requires linking pthread library (-lpthread) in Code::Blocks ('sudo apt install codeblocks'). In macOS don't use Code::Blocks. Instead extract/copy src to home folder, then open Terminal.app, enter 'cd src', then 'g++ -std=c++17 -O3 ./VanityTXID.cpp'. macOS will download & install g++ if needed. Then rename the resulting 'a.out' to 'VanityTXID-Plugin' and it's ready to go inside the zip if you want to check your own build's hash rate. Same for VanityP2SH.

Windows project files with working example parameters are included, so others can build & run immediately. There's a serious issue when it comes to deterministic builds which are verifiably identical to the source code. Checksums change with every build, whereas the exact number of Bytes stays the same, e.g. 86,016 bytes.

Linux requires eSpeak for TTS (enter 'sudo apt install espeak' in terminal). The latest version of VirtualBox gives good hash rates for all OSs. I did a native Linux test and speed as the same as for WIN10, so Code::Blocks' MinGW is probably fine.

Windows users can compare 64-bit to 32-bit performance by replacing all binaries manually from the zip. 64-bit binaries were 12% faster in a test (1.95/1.74).

v1.5.1: SHA256 Checksum: 1f16f32ea4921a16aa1d424b0b15a4765ef237b44540e0117d48fa3e51643beb
- Support for SLP Ed. v3.6.6 re-instated! I just prefer 3.6.7 (pre-releases). Screenie for macOS added.
- Max sized Scripts can now be displayed after vanity address generation.
- All new executables now enable any number of threads without any bugs. Surprisingly 8 are just as fast as 64, so we weren't missing out on anything. Instead of including mutex, it's much better to pass pointer/s to each thread so they report back. I prefer to time only in Python.
- Combined some simple lines of Python code, and reversed some simple 'for' loops using set notation.
- Technically a new Icon.webp where the ₿ is animated & shrunk to 32p before being placed on top of the colored circles.
- As usual please restart EC during update (re-install).

v1.5.0:
- Vanity CashAddr generator now included (VanityP2SH). It can "vanitize" any smart contract. It's about quadruple the speed of VanitygenCash, if using only CPU. Only 1 address at a time can be generated, currently. e.g. www.blockchain.com/bch/address/pqqqqqqfucku9gl2l5vtsu8dzmllqg9xn5z34kcu80
- Contacts instead of Address Labels. To use old VanityTXID addresses please re-generate them by 1st clearing the CashAddr Pattern, enter correct conversion address, then press Generate button and maybe delete old label. User should make a backup of the wallet, which contains the VanityTXID addresses, to avoid a lot of work reproducing vanity addresses (deterministically) from seed phrase. Eventually the contacts should be labelled too, but the SLP Ed. doesn't show Contact labels.
- Color changing TabIcon. New shade of green from bitcoincashpodcast.com
- Copy-pasteable labels, incl. hash rate.
- .notify & .activateWindow combined.
- New buttons, e.g. 'Search Contacts'. Still under 500 lines of Python! I've also slightly improved C++ code.
- Users of SLP Ed. 3.6.6 would need to update to a 3.6.7 pre-release (eg dev5) to continue using this plugin.

v1.4.1:
- Example button near title, which immediately demonstrates VanityTXID with a real example.
- Appended time to hash rate. More decimals so at least one non-0 digit occurs.
- window.show_message whenever there's a problem.
- .setToolTip for many QtWidgets.
- Animated Icon.webp. I've checked it uses 0% of CPU even with multiple wallets. It's just a BCH logo minute clock (1 FPS). I hope other plugins can do something more creative with the idea (playing movies inside a crypto wallet).
- Added std::once_flag in C++ which now simplifies Python decoding of subprocess communication. Provide error msg if someone double clicks on exe. Simpler C++, with goto. Eliminated std::stringstream and compat/cpuid.h. Some improvements are thanks to pull request by cculianu. Speed may be like 0.1% faster; build sizes are smaller. A serious issue is whether we should switch to vectors instead of arrays. I chose arrays because vectors seem less quick.
- Lack of espeak in Linux now unchecks the TTS box.

v1.4.0:
- ~31% speed increase by using Bitcoin Core's CSHA256 C++ code. Binary sizes are all much larger now. I've removed the zedwood license. In a future update I might bring it back as a UI selection, since zedwood probably wins on simplicity (imagine having to write every line yourself). Users might want to select between CryptoPP, OpenSSL, Bitcoin Core & zedwood, to check the hash rates.
- BugFix: Windows TTS now uses PowerShell -C instead of MSHTA (MicroSoft HTml App.) since the latter isn't allowed on 32-bit WIN10 Home N.
- Improved Python script. Only ever extract binaries from zip once, on enable (faster startup). Disabling plugin still removes all binaries.
- BugFix: Hash rate was always over by ~1% (3*1/255) due to 'for' loops failing to catch a few used nonce bytes at #255 (or -1). I was just about to switch back from the new 'do' loops, due to them being 1% slower!
- Random espeak pitch now in Linux, which is the synth version of random voice. BugFix: Lack of espeak no longer throws an error.
- WPM (POSix) now exponential against Rate index. Default @ Rate 5. Max WPM reduced to 450.
- Language Translator not working (module can only handle one word at a time).

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

