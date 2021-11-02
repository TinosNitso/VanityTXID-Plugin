#include "crypto/sha256.cpp"    //That code is copyrighted by Bitcoin Core.

#include <cstdio>
#include <cstdlib>
#include <mutex>
#include <thread>
#include <vector>

static const signed char hexTable[256] = {
    -1, -1,  -1,  -1,  -1,  -1,  -1,  -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1,  -1,  -1,  -1,  -1,  -1,  -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1,  -1,  -1,  -1,  -1,  -1,  -1, -1, -1, -1, -1, -1, -1, -1, -1,
    0,  1,   2,   3,   4,   5,   6,   7,  8,  9,  -1, -1, -1, -1, -1, -1,
    -1, 0xa, 0xb, 0xc, 0xd, 0xe, 0xf, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1,  -1,  -1,  -1,  -1,  -1,  -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, 0xa, 0xb, 0xc, 0xd, 0xe, 0xf, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1,  -1,  -1,  -1,  -1,  -1,  -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1,  -1,  -1,  -1,  -1,  -1,  -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1,  -1,  -1,  -1,  -1,  -1,  -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1,  -1,  -1,  -1,  -1,  -1,  -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1,  -1,  -1,  -1,  -1,  -1,  -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1,  -1,  -1,  -1,  -1,  -1,  -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1,  -1,  -1,  -1,  -1,  -1,  -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1,  -1,  -1,  -1,  -1,  -1,  -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1,  -1,  -1,  -1,  -1,  -1,  -1, -1, -1, -1, -1, -1, -1, -1, -1,
};

static inline
uint8_t FromHexTup(const char hex[2]) {   //One byte return. Assumes valid input.
    const uint8_t nibHi = hexTable[uint8_t(hex[0])];
    const uint8_t nibLo = hexTable[uint8_t(hex[1])];
    return (nibHi << 4) | nibLo;
}

static inline
uint8_t Hex2Num(const char *str) {
    char *end;
    return std::strtoul(str, &end, 16 /* base */);
}

static
std::vector<uint8_t> FromHex(const std::string &hex){
    const size_t N = hex.size();
    const size_t OutN = (N+1) / 2;
    std::vector<uint8_t> ret;
    ret.reserve(OutN);
    for (size_t i = 0; i < N; i += 2)
        ret.push_back(FromHexTup(hex.data() + i));
    return ret;
}

void Exit(const std::vector<uint8_t> &txn){  //Using an Exit function could generalize to a variable nonce size.
    for (const uint8_t byte : txn)
        std::printf("%02hhx", byte);
    std::printf("\n");
    std::exit(0);
}


void Hasher(const size_t ThreadN, const size_t Threads, char **argv) {
    const std::vector<uint8_t> NoncePos = FromHex(argv[2]);
    const size_t Pos = NoncePos[0]<<16 | NoncePos[1]<<8 | NoncePos[2];

    const std::string PatternStr{argv[3]};
    const size_t PatternLen = PatternStr.length();
    const bool PatternOdd = PatternLen % 2;
    const uint8_t PatternSize = PatternLen / 2; // In bytes, floor for odd, and 0 for singletons.
    const std::vector<uint8_t> PatternVar = FromHex(PatternStr);
    const uint8_t* Pattern = PatternVar.data();
    const uint8_t PatternEnd = Hex2Num(PatternStr.data() + PatternLen-1);

    const std::string TxHexStr{argv[4]};
    const size_t TXSize = TxHexStr.length() / 2;
    std::vector<uint8_t> TXn = FromHex(TxHexStr);

    bool Finished;  //Variable initializations.
    int8_t CheckByte;
    uint8_t SHA256[32];
    CSHA256 SHA256C;
    TXn[Pos]=ThreadN;   //This byte encodes the winning thread.
    do{do{do{do{do{do{do{do{    //'for' loops can't get to byte #255.
        SHA256C.Write(TXn.data(), TXSize);
        SHA256C.Finalize(SHA256);
        SHA256C.Reset();
        SHA256C.Write(SHA256,0x20);
        SHA256C.Finalize(SHA256);
        SHA256C.Reset();
        Finished=true;
        for (CheckByte=0;CheckByte<PatternSize;CheckByte++)
            Finished=Finished and Pattern[CheckByte]==SHA256[31-CheckByte];
        if (PatternOdd)
            Finished=Finished and PatternEnd==SHA256[31-PatternSize]>>4;
        if (Finished) {
            static std::once_flag EnsureOnly1Exit;
            // ensure that if 2 threads happen to find a solution simultaneously, only 1 wins
            std::call_once(EnsureOnly1Exit, Exit, TXn);
            return; // not normally reached unless there is a race condition
        }
    TXn[Pos+7]++;}while(TXn[Pos+7]);    //This byte changes the most.
    TXn[Pos+6]++;}while(TXn[Pos+6]);
    TXn[Pos+5]++;}while(TXn[Pos+5]);
    TXn[Pos+4]++;}while(TXn[Pos+4]);
    TXn[Pos+3]++;}while(TXn[Pos+3]);
    TXn[Pos+2]++;}while(TXn[Pos+2]);
    TXn[Pos+1]++;}while(TXn[Pos+1]);
    TXn[Pos]+=Threads;}while(TXn[Pos]>=Threads);    //Finish if passed 255.
}

int main(int argc, char **argv) {
    if (argc < 5) {
        std::fprintf(stderr, "Please pass 4 args to this program\n");
        return -1;
    }
    const size_t nThreads = Hex2Num(argv[1]) + 1;
    std::vector<std::thread> threads;
    threads.reserve(nThreads);
    for (size_t n = 0; n < nThreads; ++n)
        threads.emplace_back(Hasher, n, nThreads, argv);
    // block forever, waiting for at least 1 thread to succeed
    for (auto & thr : threads)
        thr.join();
}
