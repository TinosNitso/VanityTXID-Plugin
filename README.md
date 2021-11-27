# VanityTXID-Plugin

![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshots/v1.6.1.png)

v1.6.1 [token](https://simpleledger.info/token/00000006be2026dc68bf896783cb05c8bf65e7d0e44d8245e458657ed427498b) genesis used nonce '07000000038a0bcb', which corresponded to the 8th thread, & had hash rate 1.2 MH/s for 433B txn. I suspect assembly code might be a few times faster than sha256.cpp (BCHN). For my i7-2600 CPU, I've read estimates ranging from 5 to 24 MH/s for an 80B block header. For 197B I get nearly 2.0 MH/s, & 6.2 MH/s is for address generation (quadruple the speed of [VanitygenCash](https://github.com/cashaddress/vanitygen-cash/releases/tag/0.26)).

SLP Edition versions **3.6.7-dev6** & 3.6.7-dev5 (for macOS) don't use up a CPU processor in the background, unlike 3.6.6. The pre-releases also have newer code. The CPU usage issue can arise on all 3 OSs.

![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshots/v1.6.0.png)

![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshots/v1.5.1.png)

Generate custom SHA256 Checksums for any file. Also generate txn IDs starting with a specific pattern, using a standard wallet + plugin & watching-only wallet. Also generate vanity addresses for any Script (smart contract). Available for Electron Cash (incl. SLP Edition) on Windows, Linux & macOS. Written in Python, & C++ for the miner. To install the latest version download "VanityTXID-Plugin.zip" above, or from the proper release. Using this plugin users can create and send SLP tokens with custom token/txn ID, like this PoW NFT (minted in about 30secs): https://simpleledger.info/token/00000002dad1d1f7e12cb4fc6239a1223ed29470a909a8e8078ee51f1b5ae3a9

One issue is that **0-conf** doesn't apply to the TXID itself. The payment amount can't be changed, but the TXID & message can change before confirmation. If it ever fails, the contract can be improved, or else mining pools can mine the vanity TXID directly in return for a confidential fee. eg a new version can include simple nonce checksum/s, s.t. miners can't easily deduce a vanity contract is being used. A "smarter" contract could also sign 0-conf message using OP_CHECKDATASIG.

Code::Blocks project files with working example parameters are included in the *src* folder, so others can build & run immediately, for themselves. There's a serious issue when it comes to **deterministic** builds which are verifiably identical to the source code. Checksums change with every build, whereas the exact number of Bytes stays the same, e.g. 86,016B+8B.

Linux requires eSpeak for TTS (enter 'sudo apt install espeak' in terminal). The latest version of VirtualBox gives good hash rates for all OSs. I did a native Linux test and speed as the same as for WIN10, so Code::Blocks' MinGW is probably fine.

[Here](https://www.blockchain.com/bch/tx/000000e29285f0f77af2b29efb48060d5ede9c48b84c8003d36472f759cff9ce) is an example of a vanity TXID spending from a vanity [address](https://www.blockchain.com/bch/address/pqqqqqqsres95zmdsrvq7pmv66cy8azeq5n7q35suu) whose Script is exactly 520B, containing 505 0-bytes (1010 0s in hex). Remember that the stack must finish with only 1 item, which can't be a vector containing only 0s. Unfortunately that exact address isn't secure, due to the custom Script I made (security just takes longer to code). An example of a 520B message with vanity TXID is [here](https://www.blockchain.com/bch/tx/00000003ace42ee6d165eb3b37d27b42703cb0a56ce2990c60a84e01e78ae6d7). A vanity covenant, signed by private key=**1**, is spent [here](https://www.blockchain.com/bch/tx/d39c16d3ec66b7fb3814c98fe058af8ef8848eabfdfb036f72897efca9c353f8).

Windows users can compare 64-bit to 32-bit performance by replacing all binaries manually from the zip. 64-bit binaries were **12%** faster in a test (1.95/1.74).

VanityTXID.cpp & VanityTXID.rc are compiled together using -O3 -s -march=corei7 g++.exe compiler flags. Same for VanityP2SH. All .dll libraries are extracted from 'codeblocks-20.03mingw-nosetup.zip' & 'codeblocks-20.03-32bit-mingw-32bit-nosetup.zip'. Linux compiling doesn't use Icon.rc, and requires linking pthread library (-lpthread) in Code::Blocks ('sudo apt install codeblocks'). In macOS don't use Code::Blocks. Instead extract/copy src to home folder, then open Terminal.app, enter 'cd src', then 'g++ -std=c++17 -O3 ./VanityTXID.cpp'. macOS will download & install g++ if needed. Then rename the resulting 'a.out' to 'VanityTXID-Plugin' and it's ready to go inside the zip if you want to check your own build's hash rate. Same for VanityP2SH & VanityHash.

There's currently a bug when the user selects multiple files **and** enters an invalid hex pattern at the same time. Will be fixed in next version. 'ac7777' isn't as efficient as 'ad75', so that would shave a byte off all vanity txns. File sizes larger than 2GB might be possible. printf("%02x",...) should be improved. Base58 is conceivable. VanityTXID eventually needs a Command Line Interface.

I've taken a break from updates to learn about covenant introspection. I've generated a couple vanity covenants, like *preturn*:
https://blockchain.com/bch/address/preturn0e8y9tplrlelk7yu5av878r0nfqsguhgnrv

I don't like the CashScript or Spedn compilers, so I'm writing all the **assembly** code myself. This example takes about 9 lines of elegant code. It can return whatever coin is sent to it, but only when a Schnorr sig is used by a P2PKH sender, and the fee must be exactly 8 bits. It requires three data pushes: Parent TX, preimage, & signature. Before making such covenants work fully automatic, I need to improve the code so that Schnorr isn't essential etc. The private key is 1, and the compressed public key is just the group generator. Technically XMR (& other) swap contracts don't require such introspection.

v1.6.1: SHA256 Checksum **0000a04841563dd64bb2930ca7f296a2c152643de5b9df6c4c21c9a14d96b8eb**
- Support for EC v3.6.6 re-enabled. v1.6.0 added a tail to its own zip, which wasn't allowed by EC-v3.6.6 (nor is adding archive comments using WinRAR). 
- VanityHash now optionally uses a password, "VanityHashNonceF", to decide which bytes to vary, instead of just adding a tail every time.
- All new builds with proper memory allocation. Max file size ~2GB. Unfortunately using too many threads can cause a power failure to the CPU. Each thread demands enough RAM to work a copy of the file. I've tested over 1.7GB with 4 threads (under 3 minutes for Pattern '0', but .iso requires the "password" be placed somewhere within it).
- Can now vanitize multiple files (document batch). Assumes wallet has permission to create a new folder. No files are ever renamed.
- Drag & Drop for many files! Dropping during current process terminates the old one 1st. Files only, no folders. Drag & drop may be broken on Linux, but works fine on macOS.
- Read-only QCheckBox for Script.
- Bugfix where the VanityHash program keeps running if someone closes the wallet (oops). Added digit to hash rate, round(_,6). Much more elegant Python script, including .join()
- Button icons which tick only during execution. (Pausable movies...)
- All executable & WebP files now have SHA256 checksums starting with 0000, generated using 8B tails. The plugin itself is a zip & uses the password technique instead (hash rate over 300 H/s).
- As usual, please restart EC after uninstalling previous version. 

v1.6.0: SHA256 Checksum: 00003449a1e19a94d82dc7185c1845802c6c3c8aebd67e8083243f5415d9dde1 (0.4 kH/s · 7 mins)
- VanityHash, now included, allows vanity checksums for any file. Try it out! The plugin's .zip's checksum now starts with 0000. This allows vanity checksums for Token Documents, BFP uploads, etc. Drag & drop file may be in the next version. An 8B nonce is appended to the end of the file.
- Button icons. Address generator MessageBox improved. No nonce for CashAddr Pattern 'P' (same as 'p'). 
- In C++, 'goto Finish' moved to better place.

v1.5.1:
- Support for SLP Ed. v3.6.6 re-instated! I just prefer 3.6.7 (pre-releases). Screenie for macOS added.
- Max sized Scripts can now be displayed after vanity address generation.
- All new executables now enable any number of threads without any bugs. Surprisingly 8 are just as fast as 64, so we weren't missing out on anything. Instead of including mutex, it's much better to pass pointer/s to each thread so they report back. I prefer to time only in Python.
- Combined some simple lines of Python code, and reversed some simple 'for' loops using set notation.
- Technically a new Icon.webp where the ₿ is animated & shrunk to 32p before being placed on top of the colored circles.

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

