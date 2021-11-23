#include <fstream>
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
void Hasher(uint8_t ThreadN,bool *Bool, uint64_t *Nonce, char* chars, const int Pos, const int gcount, char **argv) {
    int16_t ThreadsN=FromHex(argv[1])[0]+1;
    const char PatternLen=std::string(argv[2]).length();
    const uint8_t* Pattern=FromHex(argv[2]);

    uint8_t* File=new uint8_t[gcount];  //Each thread should make its own, or they might interfere.
    int Int=0;
    for (;Int<gcount;Int++)File[Int]=chars[Int];
    if (Int!=Pos)
    File[Pos]=ThreadN;  //This Byte encodes the winning thread.
    for (Int=Pos+1;Int<Pos+8;Int++) File[Int]=0;

    int8_t Byte;
    std::ofstream ofstream;
    CSHA256 SHA256C;
    uint8_t* SHA256 = new uint8_t[32];
    do{do{do{do{do{do{do{do{
        SHA256C.Reset().Write(File,gcount).Finalize(SHA256);
        for (Byte=0;Byte<PatternLen>>1;Byte++)
            if (Pattern[Byte]!=SHA256[Byte]) goto Continue;
        if(PatternLen%2)
            if(Pattern[Byte]!=SHA256[Byte]>>4) goto Continue;
        if(*Bool) goto Finish;  //Double check.

        *Bool=true;
        ofstream.open(argv[4], std::fstream::binary);
        for (Int=0;Int<gcount;Int++) ofstream << File[Int];
        ofstream.close();
        for (Byte=0;Byte<32;Byte++) printf("%02x", SHA256[Byte]);

        Continue: if(*Bool) goto Finish;
    File[Pos+7]++;}while(File[Pos+7]);    //This byte changes the most.
    File[Pos+6]++;}while(File[Pos+6]);
    File[Pos+5]++;}while(File[Pos+5]);
    File[Pos+4]++;}while(File[Pos+4]);
    File[Pos+3]++;}while(File[Pos+3]);
    File[Pos+2]++;}while(File[Pos+2]);
    File[Pos+1]++;}while(File[Pos+1]);
    File[Pos]+=ThreadsN;}while(File[Pos]>=ThreadsN);    //Finish if passed 255.

    Finish:
        *Nonce=(uint64_t) File[Pos]/ThreadsN <<8*7;
        for (Byte=1;Byte<8;Byte++) *Nonce |= (uint64_t) File[Pos+Byte]<<8*(7-Byte);
}
int main(int argc , char **argv){
    if (argc < 4) {
        printf("Please pass 4 args to this program, or else use wallet plugin. Pressing 'Enter' will return. ");
        getchar(); //If anyone double clicks on exe, they can read the message.
        return 0;
    }
    std::ifstream ifstream(argv[3],std::fstream::binary);
    ifstream.ignore(std::numeric_limits<int>::max());
    int gcount = ifstream.gcount();
    char* chars=new char[gcount+8]; //Need an extra 8B allocation just in case.
    ifstream.seekg(0);
    ifstream.read(chars,gcount);
    ifstream.close();

    std::string Nonce("VanityHashNonce");  //To use this feature, Nonce must appear somewhere in the file (e.g. .zip) to be vanitized. Otherwise we just append a tail. Unlike WinRAR, many old programs don't support tails or archive comments.
    Nonce+="F"; //I've verified that the binary will ruin its own executable if "VanityHashNonce""F" is written on one line. It must generate its own executable Checksum.
    int Pos = std::string(chars,chars+gcount).find(Nonce);  //Nonce position.
    if (Pos<0){
        Pos=gcount;
        gcount+=8;
    }
    bool Bool=false;    //Bool flips when finished.
    int16_t ThreadsN=FromHex(argv[1])[0]+1;
    int16_t ThreadN=0;
    uint64_t* Nonces = new uint64_t[ThreadsN+1];
    std::thread* Threads = new std::thread[ThreadsN];
    for (;ThreadN<ThreadsN;ThreadN++) Threads[ThreadN]=std::thread(Hasher,ThreadN,&Bool,&Nonces[ThreadN],chars,Pos,gcount,argv);

    Nonces[ThreadsN]=ThreadsN; //Sum total in final element. All threads misreport nonce total by 1, because that's simpler.
    for (ThreadN=0;ThreadN<ThreadsN;ThreadN++){
            Threads[ThreadN].join();
            Nonces[ThreadsN]+=Nonces[ThreadN];
    } printf(" %llx",Nonces[ThreadsN]);    //Report back only the total # of nonces, after Hash.
}
