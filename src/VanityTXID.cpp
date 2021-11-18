#include <thread>
#include "bitcoin-cash-node/crypto/sha256.cpp"

const uint8_t hexList[]={0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,3,4,5,6,7,8,9,0,0,0,0,0,0,0,0xA,0xB,0xC,0xD,0xE,0xF,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0xa,0xb,0xc,0xd,0xe,0xf};
uint8_t* FromHex(std::string Hex){  //Some claim std::stringstream is "slow", so I'm using hexList instead.
    const int Len=Hex.length();
    uint8_t* Return = new uint8_t[(Len+1)>>1];
    for(int Ind=0;Ind<Len-1;Ind+=2) Return[Ind>>1]=hexList[(uint8_t)Hex[Ind]]<<4 | hexList[(uint8_t)Hex[Ind+1]];
    if (Len%2) Return[Len>>1]=hexList[(uint8_t)Hex.back()];
    return Return;
}
void Hasher(uint8_t ThreadN,bool *Bool, uint64_t *Nonces, char **argv) {
    int16_t ThreadsN=FromHex(argv[1])[0]+1;
    uint8_t* NoncePos=FromHex(argv[2]);
    const int Pos=NoncePos[0]<<16 | NoncePos[1]<<8 | NoncePos[2];   //Pos may need 3B for large TXn.

    const char PatternLen=std::string(argv[3]).length();
    const uint8_t* Pattern=FromHex(argv[3]);

    const int TXSize=std::string(argv[4]).length()>>1;
    uint8_t* TXn=FromHex(argv[4]);
    TXn[Pos]=ThreadN;   //This byte encodes the winning thread.

    CSHA256 SHA256C;
    uint8_t SHA256[32];
    int8_t CheckByte;
    do{do{do{do{do{do{do{do{    //'for' loops can't get to byte value 255, and cause hash rate miscalculations (1% over).
        SHA256C.Reset().Write(TXn,TXSize).Finalize(SHA256);
        SHA256C.Reset().Write(SHA256,32).Finalize(SHA256);

        if(*Bool) goto Finish;
        for (CheckByte=0;CheckByte<PatternLen>>1;CheckByte++)
            if (Pattern[CheckByte]!=SHA256[31-CheckByte]) goto Continue;
        if(PatternLen%2)
            if(Pattern[CheckByte]!=SHA256[31-CheckByte]>>4) goto Continue;
        if(*Bool) goto Finish;  //Double check.
        *Bool=true;
        for (int Ind=0;Ind<TXSize;Ind++) std::printf("%02x", TXn[Ind]); //Thanks to cculianu for suggesting std::printf
        Continue:
    TXn[Pos+7]++;}while(TXn[Pos+7]);    //This byte changes the most.
    TXn[Pos+6]++;}while(TXn[Pos+6]);
    TXn[Pos+5]++;}while(TXn[Pos+5]);
    TXn[Pos+4]++;}while(TXn[Pos+4]);
    TXn[Pos+3]++;}while(TXn[Pos+3]);
    TXn[Pos+2]++;}while(TXn[Pos+2]);
    TXn[Pos+1]++;}while(TXn[Pos+1]);
    TXn[Pos]+=ThreadsN;}while(TXn[Pos]>=ThreadsN);    //Finish if passed 255.

    Finish: *Nonces=(uint64_t) TXn[Pos]/ThreadsN <<8*7;
    for (CheckByte=1;CheckByte<8;CheckByte++) *Nonces |= (uint64_t) TXn[Pos+CheckByte]<<8*(7-CheckByte);
}
int main(int argc , char **argv){
    if (argc < 5) {
        std::fprintf(stderr, "Please pass 4 args to this program, or else use wallet plugin. Pressing 'Enter' will return. ");
        std::getchar(); //If anyone double clicks on exe, they can read the message.
        return 1;
    }
    bool Bool=false;    //Bool flips when finished.
    int16_t ThreadsN=FromHex(argv[1])[0]+1;
    int16_t ThreadN;
    uint64_t Nonces[ThreadsN+1];
    std::thread Threads[ThreadsN];
    for (ThreadN=0;ThreadN<ThreadsN;ThreadN++) Threads[ThreadN]=std::thread(Hasher,ThreadN,&Bool,&Nonces[ThreadN],argv);

    Nonces[ThreadsN]=ThreadsN; //Sum total in final element. All threads misreport nonce total by 1, because that's simpler.
    for (ThreadN=0;ThreadN<ThreadsN;ThreadN++){
            Threads[ThreadN].join();
            Nonces[ThreadsN]+=Nonces[ThreadN];
    } std::printf(" %llx",Nonces[ThreadsN]);    //Report back only the total # of nonces, after TXn. 64 threads are no faster than 8, it turns out.
}
