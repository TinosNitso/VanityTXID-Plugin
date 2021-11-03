#include "crypto/sha256.cpp"    //Copy-pasted from BCHN.

#include <cstdio>
#include <mutex>
#include <thread>
#include <vector>

static std::once_flag EnsureOnly1Exit;   // ensure that if 2 threads happen to find a solution simultaneously, only 1 wins
static void Exit(const std::vector<uint8_t> &txn){
    for (uint8_t byte : txn) std::printf("%02hhx", byte);
    exit(0);
}
static void Hasher(const size_t &ThreadN, const size_t &nThreads, const int &Pos, const std::vector<uint8_t> &Pattern, const bool &PatternOdd, std::vector<uint8_t> TXn) {
    const uint8_t PatternSize = Pattern.size()-PatternOdd;  //I mean the byte size without the nibble at the end.
    const uint8_t PatternEnd=Pattern.back();
    const int TXSize=TXn.size();

    bool Finished;  //Variable initializations.
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
        for (uint8_t CheckByte = 0; CheckByte < PatternSize; ++CheckByte) Finished=Finished and Pattern[CheckByte]==SHA256[31-CheckByte];
        if (PatternOdd) Finished=Finished and PatternEnd==SHA256[31-PatternSize]>>4;
        if (Finished) {
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
    TXn[Pos]+=nThreads;}while(TXn[Pos]>=nThreads);    //Finish if passed 255.
}
static const uint8_t hexList[103] = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,3,4,5,6,7,8,9,0,0,0,0,0,0,0,0xa,0xb,0xc,0xd,0xe,0xf,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0xa,0xb,0xc,0xd,0xe,0xf};
static std::vector<uint8_t> FromHex(const std::string &hex){
    const size_t N = hex.size();
    std::vector<uint8_t> ret;
    ret.reserve((N+1)/2);
    for (size_t i = 0; i < N-1; i += 2) ret.emplace_back(hexList[uint8_t(hex[i])]<<4 | hexList[uint8_t(hex[i+1])]);
    if (N%2) ret.emplace_back(hexList[uint8_t(hex[N-1])]);
    return ret;
}
int main(int argc, char **argv) {
    if (argc < 5) {
        std::fprintf(stderr, "Please pass 4 args to this program\n");
        return -1;
    }
    const size_t nThreads = FromHex(argv[1])[0] + 1;
    const std::vector<uint8_t> NoncePos = FromHex(argv[2]);
    const int Pos = NoncePos[0]<<16 | NoncePos[1]<<8 | NoncePos[2];

    const std::vector<uint8_t> Pattern = FromHex(argv[3]);
    const bool PatternOdd = std::string(argv[3]).length() % 2;

    std::vector<uint8_t> TXn = FromHex(argv[4]);
    std::vector<std::thread> threads;
    threads.reserve(nThreads);
    for (size_t n = 0; n < nThreads; ++n) threads.emplace_back(Hasher, n, nThreads, Pos, Pattern, PatternOdd, TXn);  //I'm only doing it this way because others seem to care about the "speed" of FromHex.
    threads[0].join();// block forever, waiting for at least 1 thread to succeed
}
