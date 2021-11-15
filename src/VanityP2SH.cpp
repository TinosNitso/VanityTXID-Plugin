#include <mutex>
#include <thread>
#include "bitcoin-cash-node/crypto/sha256.cpp"
#include "bitcoin-cash-node/crypto/ripemd160.cpp"

const uint8_t hexList[]={0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,3,4,5,6,7,8,9,0,0,0,0,0,0,0,0xA,0xB,0xC,0xD,0xE,0xF,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0xa,0xb,0xc,0xd,0xe,0xf};
uint8_t* FromHex(std::string Hex){  //Some claim std::stringstream is "slow", so I'm using hexList instead.
    const int Len=Hex.length();
    uint8_t* Return = new uint8_t[(Len+1)>>1];
    for(int Ind=0;Ind<Len-1;Ind+=2) Return[Ind>>1]=hexList[(uint8_t)Hex[Ind]]<<4 | hexList[(uint8_t)Hex[Ind+1]];
    if (Len%2) Return[Len>>1]=hexList[(uint8_t)Hex.back()];
    return Return;
}
const uint8_t CashAddrList[]={0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,15,0,10,17,21,20,26,30,7,5,0,0,0,0,0,0,0,29,0,24,13,25,9,8,23,0,18,22,31,27,19,0,1,0,3,16,11,28,12,14,6,4,2,0,0,0,0,0,0,29,0,24,13,25,9,8,23,0,18,22,31,27,19,0,1,0,3,16,11,28,12,14,6,4,2};
std::once_flag once_flag;   // ensure that if 2 threads happen to find a solution simultaneously, only 1 wins
void Exit(uint8_t* Script,int16_t SSize){
    for (int16_t Ind=0;Ind<SSize;Ind++) std::printf("%02x", Script[Ind]);
    exit(0);
}
void Hasher(uint8_t ThreadN,char **argv) {
    int16_t ThreadsN=FromHex(argv[1])[0]+1;
    uint8_t* NoncePos=FromHex(argv[2]);
    const int16_t Pos=NoncePos[0]<<8 | NoncePos[1];    //520B SSize limit.

    std::string String=std::string(argv[3]);
    const uint8_t Bytes=(2+(String.length()-2)*5)/8+bool(String.length()%8);   //How many Bytes do we need to check? The last one gets shifted by 1->7 unless Pattern 8 or 16 long.
    uint8_t Pattern[Bytes];
    Pattern[0]=0;
    int8_t Byte=0;
    int8_t Shift=11;    //Bit-Shift amount btwn 0 & 7. 11 is just an initialization to get the 1st 2b right (q, p, z or r). There should be a more elegant technique than what I've done here.
    String.erase(0,1);  //1st 'p' is irrelevant.
    for (uint8_t Char: String){
        if(Shift>=5){
            Shift-=5;
            Pattern[Byte]|=CashAddrList[Char]<<Shift;
        }else{
            Pattern[Byte]|=CashAddrList[Char]>>(5-Shift);    //-ve shift.
            Byte++;
            Shift+=3;
            Pattern[Byte]=CashAddrList[Char]<<Shift;
    }}
    Pattern[Byte]=Pattern[Byte]>>Shift;  //Shift last Byte in advance of loops (Shift could be 0).

    const int SSize=std::string(argv[4]).length()>>1;
    uint8_t* Script=FromHex(argv[4]);
    Script[Pos]=ThreadN;   //This byte encodes the winning thread.

    CSHA256 SHA256C;
    CRIPEMD160 RIPEMD160C;
    uint8_t SHA256[32];
    uint8_t RIPEMD160[20];
    do{do{do{do{do{do{do{do{
        SHA256C.Reset().Write(Script,SSize).Finalize(SHA256);
        RIPEMD160C.Reset().Write(SHA256,32).Finalize(RIPEMD160);
        for(Byte=0;Byte<Bytes-1;Byte++)
            if (Pattern[Byte] != RIPEMD160[Byte]) goto GoTo;
        if (Pattern[Byte] != RIPEMD160[Byte]>>Shift) goto GoTo;  //Shift out irrelevant bits at the end (checks final byte even when bit-shifting by zero).
        std::call_once(once_flag, Exit, Script, SSize);
        GoTo:
    Script[Pos+7]++;}while(Script[Pos+7]);    //This byte changes the most.
    Script[Pos+6]++;}while(Script[Pos+6]);
    Script[Pos+5]++;}while(Script[Pos+5]);
    Script[Pos+4]++;}while(Script[Pos+4]);
    Script[Pos+3]++;}while(Script[Pos+3]);
    Script[Pos+2]++;}while(Script[Pos+2]);
    Script[Pos+1]++;}while(Script[Pos+1]);
    Script[Pos]+=ThreadsN;}while(Script[Pos]>=ThreadsN);    //Finish if passed 255.
}
int main(int argc , char **argv){
    if (argc < 5) {
        std::fprintf(stderr, "Please pass 4 args to this program, or else use wallet plugin. Pressing 'Enter' will return. ");
        std::getchar(); //If anyone double clicks on exe, they can read the message.
        return 1;
    }
    int16_t ThreadsN=FromHex(argv[1])[0]+1;
    std::thread Threads[ThreadsN];
    for (uint8_t ThreadN=0;ThreadN<ThreadsN;ThreadN++) Threads[ThreadN]=std::thread(Hasher,ThreadN,argv);
    Threads[0].join(); // ThreadN 0 is main itself.
}
