#include "crypto/sha256.cpp"    //Copy-pasted from BCHN.

#include <cstdio>
#include <mutex>
#include <thread>
#include <vector>

std::once_flag EnsureOnly1Exit;   // ensure that if 2 threads happen to find a solution simultaneously, only 1 wins
void Exit(const std::vector<uint8_t> &txn){
    for (uint8_t byte : txn) std::printf("%02hhx", byte);
    exit(0);
}
void Hasher(uint8_t ThreadN, size_t nThreads, const size_t &Pos, const std::vector<uint8_t> &Pattern, const bool &PatternOdd, std::vector<uint8_t> TXn) {
    const size_t TXSize=TXn.size();
    bool Finished;
    uint8_t SHA256[32];
    CSHA256 SHA256C;
    TXn[Pos]=ThreadN;   //This byte encodes the winning thread.
    do{do{do{do{do{do{do{do{    //'for' loops can't get to byte value 255, and therefore lie about the hash rate by like 1%.
        SHA256C.Write(TXn.data(), TXSize);
        SHA256C.Finalize(SHA256);
        SHA256C.Reset();
        SHA256C.Write(SHA256,0x20);
        SHA256C.Finalize(SHA256);
        SHA256C.Reset();
        Finished=true;
        for (uint8_t CheckByte = 0; CheckByte < Pattern.size()-PatternOdd; CheckByte++) Finished=Finished and Pattern[CheckByte]==SHA256[31-CheckByte];
        if (PatternOdd) Finished=Finished and Pattern.back()==SHA256[32-Pattern.size()]>>4;
        if (Finished) std::call_once(EnsureOnly1Exit, Exit, TXn);
    TXn[Pos+7]++;}while(TXn[Pos+7]);    //This byte changes the most.
    TXn[Pos+6]++;}while(TXn[Pos+6]);
    TXn[Pos+5]++;}while(TXn[Pos+5]);
    TXn[Pos+4]++;}while(TXn[Pos+4]);
    TXn[Pos+3]++;}while(TXn[Pos+3]);
    TXn[Pos+2]++;}while(TXn[Pos+2]);
    TXn[Pos+1]++;}while(TXn[Pos+1]);
    TXn[Pos]+=nThreads;}while(TXn[Pos]>=nThreads);    //Finish if passed 255.
}
int hexList[103] = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,3,4,5,6,7,8,9,0,0,0,0,0,0,0,0xa,0xb,0xc,0xd,0xe,0xf,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0xa,0xb,0xc,0xd,0xe,0xf};
std::vector<uint8_t> FromHex(std::string hex){
    std::vector<uint8_t> ret;
    for (size_t i = 0; i < hex.size()-1; i += 2) ret.emplace_back(hexList[int(hex[i])]<<4 | hexList[int(hex[i+1])]);   //People claim std::stringstream is "slow", so I'm using hexList instead.
    if (hex.size()%2) ret.emplace_back(hexList[int(hex.back())]);
    return ret;
}
int main(int argc, char **argv) {
    if (argc < 5) {
        std::fprintf(stderr, "Please pass 4 args to this console app, or else don't execute it directly. It's intended for use with a wallet's Python subprocess.Popen");
        std::getchar(); //If anyone double clicks on us, they can read the message.
        return 1;
    }
    size_t nThreads = FromHex(argv[1])[0] + 1;
    std::vector<uint8_t> NoncePos = FromHex(argv[2]);
    size_t Pos = NoncePos[0]<<16 | NoncePos[1]<<8 | NoncePos[2];

    std::vector<uint8_t> Pattern = FromHex(argv[3]);
    bool PatternOdd = std::string(argv[3]).length() % 2;

    std::vector<uint8_t> TXn = FromHex(argv[4]);
    std::vector<std::thread> threads;
    for (uint8_t ThreadN = 0; ThreadN < nThreads; ThreadN++) threads.emplace_back(Hasher, ThreadN, nThreads, Pos, Pattern, PatternOdd, TXn);  //There are many arguments because others seem to care about the "speed" of FromHex.
    threads[0].join();  // threads[0] could just as well be created here, so that main is no different to any other thread.
}
