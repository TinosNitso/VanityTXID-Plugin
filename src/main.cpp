#include <iostream>
#include <sstream>
#include <thread>
#include "sha256.cpp"

std::string FromHex(std::string Hex){
    std::string String;
    int N=Hex.length();
    std::stringstream SS;
    int Char;
    if (N==1){
        SS<<std::hex<<Hex;
        SS>>Char;
        return {Char};
    } if (N%2) N-=1;
    for(int n=0;n<N/2;n++){
        SS<<std::hex<<(std::string){Hex[2*n],Hex[2*n+1]};
        SS>>Char;
        SS.clear();
        String+=Char;
    } return String;
}
void Hasher(int ThreadN,char **argv) {
    int Threads=uint8_t(FromHex(argv[1])[0])+1;
    std::string NoncePos=FromHex(argv[2]);
    std::string Pattern=argv[3];
    std::string String=FromHex(argv[4]);

    int PatternLen=Pattern.length();
    bool PatternOdd=PatternLen%2;

    std::string PatternString=FromHex(Pattern);
    int PatternSize=PatternString.length();
    if (Pattern.length()==1) PatternSize=0;
    uint8_t PatternEnd=FromHex({Pattern[PatternLen-1]})[0];
    int P1=(uint8_t)NoncePos[0]<<8 | (uint8_t)NoncePos[1];
    int P2=P1+1;
    int P3=P2+1;
    int P4=P3+1;
    int P5=P4+1;
    int P6=P5+1;
    int P7=P6+1;
    int P8=P7+1;
    bool Finished;
    int8_t CheckByte;
    std::string sha256d;
    for (String[P1]=ThreadN;String[P1]!=ThreadN-Threads;String[P1]+=Threads) {
    for (String[P2]=0;String[P2]!=-1;String[P2]++) {
    for (String[P3]=0;String[P3]!=-1;String[P3]++) {
    for (String[P4]=0;String[P4]!=-1;String[P4]++) {
    for (String[P5]=0;String[P5]!=-1;String[P5]++) {
    for (String[P6]=0;String[P6]!=-1;String[P6]++) {
    for (String[P7]=0;String[P7]!=-1;String[P7]++) {
    for (String[P8]=0;String[P8]!=-1;String[P8]++) {
        sha256d=sha256String(sha256String(String));
        Finished=true;
        for (CheckByte=0;CheckByte<PatternSize;CheckByte++)
            Finished=Finished and PatternString[CheckByte]==sha256d[31-CheckByte];
        if (PatternOdd)
            Finished=Finished and PatternEnd==(uint8_t)sha256d[31-PatternSize]>>4;
        if (Finished) break;
    }   if (Finished) break;
    }   if (Finished) break;
    }   if (Finished) break;
    }   if (Finished) break;
    }   if (Finished) break;
    }   if (Finished) break;
    }   if (Finished) break;
    };
    char Return[2*String.length()];
    for (int i = 0; i < String.length(); i++)
        sprintf(Return+2*i, "%02x", (uint8_t) String[i]);
    std::cout<<Return<<std::flush;
    system("taskkill /IM VanityTXID-Plugin.exe /F >nul 2>&1");
}
int main(int argc , char **argv){
    int Threads=(uint8_t)FromHex(argv[1])[0]+1;
    std::thread Thread[Threads];
    for (uint8_t ThreadN=0;ThreadN<Threads;ThreadN++){
        Thread[ThreadN]=std::thread(Hasher,ThreadN,argv);
    }   Thread[0].join();
}
