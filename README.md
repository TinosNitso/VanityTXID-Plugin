# VanityTXID-Plugin

Security issue: I should update to use gc.collect() to further erase all password and privkey variables, otherwise Python's del may not permamenently erase them from RAM, unless EC does it. Oops!

License issue: I failed to mention in all the releases that this project has copied from qt.py from the plugin template released by Karol Trzeszczkowski (GNU GPL v3). I don't fully understand that code, yet. github.com/KarolTrzeszczkowski/Electron-Cash-Plugin-Template

![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/Screenshot.png)

Generate txn IDs starting with a specific pattern, using a standard wallet + plugin & watching-only wallet. Currently only available for (BCH) Electron Cash on Linux & Windows. Written in Python & C++ for the miner. To install the latest version you can just download "VanityTXID-Plugin.zip" above. Using this plugin you can also create and send SLP tokens with custom token/txn ID, like this PoW NFT (minted in under 30secs): www.simpleledger.info/token/0000000f1393392b8de2cbf05e7a0ebc3d4630395e49a7c3f09174e46ce09da7

main.cpp & Icon.rc are compiled together using the -O3 compiler flag as a project build option. The three .dll libraries are extracted directly from 'codeblocks-20.03-32bit-mingw-32bit-nosetup.zip'. Linux compiler uses only main.cpp. The screenshot example has nonce '0400000002054ba8'. '04' corresponds to the fifth thread. v1.1.0 SHA256 Checksum: a6c4e675b2516cfc4c0839198126c192bbb646430c60febc4bdf5a2b198524a6

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
