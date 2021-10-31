#include <iostream>
#include <sstream>
#include <thread>
#include "crypto/sha256.cpp"    //That code is copyrighted by Bitcoin Core.

uint8_t FromHex(std::string Hex){   //One byte return.
    std::stringstream SS;
    SS<<std::hex<<Hex;
    int Return;
    SS>>Return;
    return Return;
}
void FromHex(uint8_t* Return,std::string Hex){  //Instead of returning std::string we can use first input as uint8_t* whose length is unknown.
    int N=Hex.length();
    std::stringstream SS;
    int Char;
    for(int n=0;n<N/2;n++){
        SS<<std::hex<<(std::string){Hex[2*n],Hex[2*n+1]};
        SS>>Char;
        SS.clear();
        Return[n]=Char;
}}
void Exit(const uint8_t* TXn,const uint32_t TXSize){    //Using an Exit function could generalize to a variable nonce size.
    char Return[2*TXSize];
    for (uint32_t i = 0; i < TXSize; i++)
        sprintf(Return+2*i, "%02x", TXn[i]);
    std::cout<<Return;
    exit(0);
}
void Hasher(int ThreadN,char **argv) {
    int Threads=FromHex(argv[1])+1;

    uint8_t NoncePos[3];
    FromHex(NoncePos,argv[2]);
    const uint32_t Pos=NoncePos[0]<<16 | NoncePos[1]<<8 | NoncePos[2];

    int PatternLen=std::string(argv[3]).length();
    const bool PatternOdd=PatternLen%2;
    const uint8_t PatternSize=PatternLen/2; // In bytes, floor for odd, and 0 for singletons.
    uint8_t PatternVar[PatternSize];
    FromHex(PatternVar,argv[3]);
    const uint8_t* Pattern=PatternVar;
    const uint8_t PatternEnd=FromHex({argv[3][PatternLen-1]});

    const uint32_t TXSize=std::string(argv[4]).length()/2;
    uint8_t TXn[TXSize];
    FromHex(TXn,argv[4]);

    bool Finished;  //Variable initializations.
    int8_t CheckByte;
    uint8_t SHA256[32];
    CSHA256 SHA256C;
    TXn[Pos]=ThreadN;   //This byte encodes the winning thread.
    do{do{do{do{do{do{do{do{    //'for' loops can't get to byte #255.
        SHA256C.Write(TXn,TXSize);
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
        if (Finished) Exit(TXn,TXSize);
    TXn[Pos+7]++;}while(TXn[Pos+7]);    //This byte changes the most.
    TXn[Pos+6]++;}while(TXn[Pos+6]);
    TXn[Pos+5]++;}while(TXn[Pos+5]);
    TXn[Pos+4]++;}while(TXn[Pos+4]);
    TXn[Pos+3]++;}while(TXn[Pos+3]);
    TXn[Pos+2]++;}while(TXn[Pos+2]);
    TXn[Pos+1]++;}while(TXn[Pos+1]);
    TXn[Pos]+=Threads;}while(TXn[Pos]>=Threads);    //Finish if passed 255.
}
int main(int argc , char **argv){
    int Threads=FromHex(argv[1])+1;
    std::thread Thread[Threads];
    for (uint8_t ThreadN=1;ThreadN<Threads;ThreadN++)
        Thread[ThreadN]=std::thread(Hasher,ThreadN,argv);
    Hasher(0,argv); // ThreadN 0 is main itself.
}
