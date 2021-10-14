#include <iostream>
#include <sstream>
#include <thread>
#include <unistd.h>
#include "sha256.cpp"

std::string FromHex(std::string Hex){
    std::string String;
    int N=Hex.length();
    std::stringstream SS;
    int Char;
    if (N==1){
        SS<<std::hex<<Hex;
        SS>>Char;
        return {(char)Char};
    } if (N%2) N-=1;
    for(int n=0;n<N/2;n++){
        SS<<std::hex<<(std::string){Hex[2*n],Hex[2*n+1]};
        SS>>Char;
        SS.clear();
        String+=Char;
    } return String;
}
void Exit(std::string &String){
    char Return[2*String.length()];
    for (uint32_t i = 0; i < String.length(); i++)
        sprintf(Return+2*i, "%02x", (uint8_t) String[i]);
    std::cout<<Return<<std::flush;  // flush is only needed when using a function to exit(0).
    exit(0);
}
void Hasher(int ThreadN,char **argv) {
    int Threads=uint8_t(FromHex(argv[1])[0])+1;
    std::string NoncePos=FromHex(argv[2]);
    std::string Pattern=argv[3];
    std::string String=FromHex(argv[4]);

    int PatternLen=Pattern.length();
    bool PatternOdd=PatternLen%2;

    const std::string PatternString=FromHex(Pattern);
    int PatternSizeVar=PatternString.length();
    if (Pattern.length()==1) PatternSizeVar=0;
    const int PatternSize=PatternSizeVar;   // const might be faster for some reason.
    const uint8_t PatternEnd=FromHex({Pattern[PatternLen-1]})[0];
    const uint32_t P=(uint8_t)NoncePos[0]<<16 | (uint8_t)NoncePos[1]<<8 | (uint8_t)NoncePos[2];
    bool Finished;
    int8_t CheckByte;
    std::string sha256d;
    for (String[P]=ThreadN;String[P]!=ThreadN-Threads;String[P]+=Threads) {
    for (String[P+1]=0;String[P+1]!=-1;String[P+1]++) {
    for (String[P+2]=0;String[P+2]!=-1;String[P+2]++) {
    for (String[P+3]=0;String[P+3]!=-1;String[P+3]++) {
    for (String[P+4]=0;String[P+4]!=-1;String[P+4]++) {
    for (String[P+5]=0;String[P+5]!=-1;String[P+5]++) {
    for (String[P+6]=0;String[P+6]!=-1;String[P+6]++) {
    for (String[P+7]=0;String[P+7]!=-1;String[P+7]++) {
        sha256d=sha256String(sha256String(String));
        Finished=true;
        for (CheckByte=0;CheckByte<PatternSize;CheckByte++)
            Finished=Finished and PatternString[CheckByte]==sha256d[31-CheckByte];
        if (PatternOdd)
            Finished=Finished and PatternEnd==(uint8_t)sha256d[31-PatternSize]>>4;
        if (Finished) Exit(String);
}}}}}}}}}
int main(int argc , char **argv){
    int Threads=(uint8_t)FromHex(argv[1])[0]+1;
    std::thread Thread[Threads];
    for (uint8_t ThreadN=1;ThreadN<Threads;ThreadN++)
        Thread[ThreadN]=std::thread(Hasher,ThreadN,argv);
    Hasher(0,argv); // ThreadN 0 is main itself.
}
