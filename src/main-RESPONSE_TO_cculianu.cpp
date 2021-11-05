#include <cstdio>
#include <mutex>
#include <thread>
#include "crypto/sha256.cpp"    //From BCHN.

uint8_t hexList[103] = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,3,4,5,6,7,8,9,0,0,0,0,0,0,0,0xA,0xB,0xC,0xD,0xE,0xF,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0xa,0xb,0xc,0xd,0xe,0xf};
uint8_t* FromHex(std::string Hex){  //Some claim std::stringstream is "slow", so I'm using hexList instead.
    int Len=Hex.length();
    uint8_t* Return = new uint8_t[(Len+1)/2];
    for(int Ind=0;Ind<Len-1;Ind+=2) Return[Ind/2]=hexList[(uint8_t)Hex[Ind]]<<4 | hexList[(uint8_t)Hex[Ind+1]];
    if (Len%2) Return[Len/2]=hexList[(uint8_t)Hex.back()];
    return Return;
}
std::once_flag EnsureOnly1Exit;   // ensure that if 2 threads happen to find a solution simultaneously, only 1 wins
void Exit(uint8_t* TXn,int TXSize){
    for (int Ind=0;Ind<TXSize;Ind++) std::printf("%02x", TXn[Ind]);
    exit(0);
}
void Hasher(uint8_t ThreadN,char **argv) {
    int16_t ThreadsN=FromHex(argv[1])[0]+1;
    uint8_t* NoncePos=FromHex(argv[2]);
    const int Pos=NoncePos[0]<<16 | NoncePos[1]<<8 | NoncePos[2];

    const int8_t PatternLen=std::string(argv[3]).length();
    const uint8_t* Pattern=FromHex(argv[3]);

    const int TXSize=std::string(argv[4]).length()/2;
    uint8_t* TXn=FromHex(argv[4]);
    TXn[Pos]=ThreadN;   //This byte encodes the winning thread.
    bool Finished;  //Variable initializations.
    int8_t CheckByte;
    uint8_t SHA256[32];
    CSHA256 SHA256C;
    do{do{do{do{do{do{do{do{    //'for' loops can't get to byte value 255, and cause hash rate miscalculations (1% over).
        SHA256C.Write(TXn,TXSize);
        SHA256C.Finalize(SHA256);
        SHA256C.Reset();
        SHA256C.Write(SHA256,0x20);
        SHA256C.Finalize(SHA256);
        SHA256C.Reset();

        Finished=true;
        for (CheckByte=0;CheckByte<PatternLen/2;CheckByte++) Finished=Finished and Pattern[CheckByte]==SHA256[31-CheckByte];
        if (PatternLen%2) Finished=Finished and Pattern[CheckByte]==SHA256[31-CheckByte]>>4;
        if (Finished) std::call_once(EnsureOnly1Exit, Exit, TXn, TXSize);
    TXn[Pos+7]++;}while(TXn[Pos+7]);    //This byte changes the most.
    TXn[Pos+6]++;}while(TXn[Pos+6]);
    TXn[Pos+5]++;}while(TXn[Pos+5]);
    TXn[Pos+4]++;}while(TXn[Pos+4]);
    TXn[Pos+3]++;}while(TXn[Pos+3]);
    TXn[Pos+2]++;}while(TXn[Pos+2]);
    TXn[Pos+1]++;}while(TXn[Pos+1]);
    TXn[Pos]+=ThreadsN;}while(TXn[Pos]>=ThreadsN);    //Finish if passed 255.
}
int main(int argc , char **argv){
    if (argc < 5) {
        std::fprintf(stderr, "Please pass 4 args to this console app, or else don't execute it directly. It's intended for use with a wallet's Python subprocess.Popen");
        std::getchar(); //If anyone double clicks on exe, they can read the message.
        return 1;
    }
    int16_t ThreadsN=FromHex(argv[1])[0]+1;
    std::thread Threads[ThreadsN];
    for (uint8_t ThreadN=0;ThreadN<ThreadsN;ThreadN++) Threads[ThreadN]=std::thread(Hasher,ThreadN,argv);
    Threads[0].join(); // ThreadN 0 is main itself.
}
