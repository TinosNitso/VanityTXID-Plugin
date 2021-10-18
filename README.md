# VanityTXID-Plugin

I just realized there's a 117 Byte size limit to the message. The Genesis message easily fits in, so I didn't realize! In the next update there'll be optional audio, and message text input, but removing the size limitation looks tricky.

![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshot-v1.3.0.png)

Windows users can update their SLP Edition to the pre-release 3.6.7-dev6. It has a bug-fix which makes VanityTXID work faster. It also would have required less work from me to make the plugin SLP compatible.

The screenshot for v1.3.0 involved nonce '0400000000b3479b', where '04' corresponds to the 5th thread. v1.3.0 SHA256 Checksum: 19428b63d42b1fe33e89af5f678dad88360c017331fe6ff5bea8cb1f96bdb49c

![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshot2.png)
![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshot-v1.1.0.png)
Generate txn IDs starting with a specific pattern, using a standard wallet + plugin & watching-only wallet. Available for Electron Cash on macOS, Linux & Windows. Written in Python, & C++ for the miner. To install the latest version you can just download "VanityTXID-Plugin.zip" above. Using this plugin you can create and send SLP tokens with custom token/txn ID, like this PoW NFT (minted in under 30secs): www.simpleledger.info/token/0000000f1393392b8de2cbf05e7a0ebc3d4630395e49a7c3f09174e46ce09da7

main.cpp & Icon.rc are compiled together using -O3 -s -march=corei7-avx with the gcc compiler (before I only used -O3 -s). The three .dll libraries are extracted directly from 'codeblocks-20.03-32bit-mingw-32bit-nosetup.zip'. Linux & macOS compiling don't use Icon.rc. I've now included the Windows project file with example arguments so others can build & run immediately. There's a serious issue when it comes to deterministic builds which are verifiably identical to the source code.

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

I've been trying to get some virtual machines working, but VirtualBox was too difficult, so now I'm learning to use Hyper-V. First I'm gonna test Windows XP. I think I'll try get hash rate before adding Linux support.

v1.0.2 notes:
- Nonce position can now be up to 256**2, so the input being "mined" doesn't have to be the first. (There was also a bug in the C++ binary of v1.0.1) e.g. now in www.blockchain.com/bch/tx/0000006727815232d1fd48e1988b9aea8b3e4cd060dfbe44c4a52239c71b5cd5 'deadbeef' doesn't appear until the 2nd input.
- Improved code so that raw TX hex can be repeatedly mined (copy-paste after mining, and then again etc).
- Full support for legacy P2SH form (starting with '3' instead of 'p').
- Multiple P2SH address display, but generating lots of addresses at once will be in next update.
- Added version title.

v1.0.1 notes:
- Now support uncompressed keys. e.g. www.blockchain.com/bch/tx/000000821afbda9e137ab90bf5de3cad8bf8a3bbe218b7f9c26566ec5779fd8f
- Have improved UI with labels.
- Have fixed many error reports by using try:/except: functions. Crashes honestly never happened for me at first 'cause I was testing on portable EC - it depends on the EC edition whether try:/except: is really needed. e.g. non-portable EC no longer reports error on TaskKill.
- Found Python bitcoin.int_to_hex
- del(Password) after it's used.
- 128<Thread#<256 now allowed (was bug in C++ code). I've found 256 threads might be a tiny bit faster than 8 for patterns six long.

v1.0.0 simply blocked uncompressed keys from being used, without ever burning any coins. v1.0.1 now allows any keys!
