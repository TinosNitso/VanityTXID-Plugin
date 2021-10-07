# VanityTXID-Plugin
![alt text](https://github.com/TinosNitso/VanityTXID-Plugin/blob/main/SCREENSHOT.PNG)

Generate txn IDs starting with a specific pattern, using a standard wallet + plugin & watching-only wallet. Currently only available for Electron Cash on Windows (BCH). Written in Python & C++ for the miner. To install the latest version you can just download "VanityTXID-Plugin.zip" above. Using this plugin you can also create and send SLP tokens with custom token/txn ID, like this PoW NFT: www.simpleledger.info/token/0000000f1393392b8de2cbf05e7a0ebc3d4630395e49a7c3f09174e46ce09da7

v1.0.2 notes:
- Nonce position can now be up to 256**2, so the input being "mined" doesn't have to be the first. (There was also a bug in the C++ binary of v1.0.1.) e.g. in www.blockchain.com/bch/tx/0000006727815232d1fd48e1988b9aea8b3e4cd060dfbe44c4a52239c71b5cd5 'deadbeef' doesn't appear until the 2nd input.
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
