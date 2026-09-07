// Independent exact validator: direct binary states, transition-table coordinates,
// and DFS without memoization. Completed starting positions resume atomically.
// g++ -O2 -std=c++17 -Wall -Wextra -pedantic -DSOURCE_SHA=\"...\" this.cpp -o checker
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdio>
#include <cstdint>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
#ifndef SOURCE_SHA
#define SOURCE_SHA "unidentified"
#endif
using V=std::array<int,3>;
static int B=16,N=512,maxReach=0;
static uint64_t nodes=0;
static std::vector<std::vector<int>> edge;
static std::array<int,5> menu{};
static std::string stamp(){const auto now=std::time(nullptr);char b[32];std::strftime(b,sizeof b,"%Y-%m-%dT%H:%M:%SZ",std::gmtime(&now));return b;}
static int state(int n){int s=0,sign=1;while(n){s+=sign*(n&1);sign=-sign;n>>=1;}return (s%4+4)%4;}
static V step(int r,int s){
 switch(4*r+s){
 case 1:return {1,0,5};case 6:return {0,3,5};case 11:return {-1,-2,5};case 12:return {0,-1,1};
 case 2:case 7:return {1,1,6};case 8:case 13:return {-1,-1,2};
 default:throw std::runtime_error("unexpected transition");
 }
}
static bool dfs(int n,int size){
 ++nodes;maxReach=std::max(maxReach,n);if(n>=N)return true;
 for(int d=1;d<=B;++d){
  const int id=edge[n][d-1];const bool known=std::find(menu.begin(),menu.begin()+size,id)!=menu.begin()+size;
  if(known){if(dfs(n+d,size))return true;}
  else if(size<5){menu[size]=id;if(dfs(n+d,size+1))return true;}
 }
 return false;
}
struct Record {int first;uint64_t nodes;int reach;};
int main(int argc,char**argv){try{
 if(argc>1&&std::string(argv[1])=="--help"){
  std::cout<<"Usage: checker [GAP=16] [PREFIX=512]\nOne CPU thread. Atomic checkpoints in .checkpoint-return-blocks resume completed starting positions; interrupted position restarts.\n";return 0;
 }
 if(argc>1)B=std::stoi(argv[1]);
 if(argc>2)N=std::stoi(argv[2]);
 if(B<1||B>32||N<=B||N>4096)throw std::runtime_error("invalid bounds");
 if(std::string(SOURCE_SHA)=="unidentified")throw std::runtime_error("compile with -DSOURCE_SHA containing source SHA-256");
 std::filesystem::create_directories(".checkpoint-return-blocks");
 const std::string path=".checkpoint-return-blocks/verify-"+std::to_string(B)+"-"+std::to_string(N)+"-"+std::string(SOURCE_SHA).substr(0,12)+".txt";
 std::vector<Record> records;
 if(std::filesystem::exists(path)){
  std::ifstream in(path);std::string hash;int b,n,k;in>>hash>>b>>n>>k;
  if(!in||hash!=SOURCE_SHA||b!=B||n!=N||k<0||k>B)throw std::runtime_error("incompatible checkpoint");
  for(int i=0;i<k;++i){Record r{};in>>r.first>>r.nodes>>r.reach;if(!in||r.first!=i||r.reach<r.first||r.reach>=N)throw std::runtime_error("corrupt checkpoint");records.push_back(r);}
  std::string extra;if(in>>extra)throw std::runtime_error("trailing checkpoint data");
 }
 const auto start=std::chrono::steady_clock::now();
 std::cout<<stamp()<<" start hash="<<SOURCE_SHA<<" B="<<B<<" N="<<N<<" threads=1 checkpoint="<<path<<" completed="<<records.size()<<"/"<<B<<std::endl;
 std::vector<V> P(N+B+1);P[0]={0,0,0};
 for(int n=0;n<N+B;++n){V v=step(state(n),state(n+1));for(int k=0;k<3;++k)P[n+1][k]=P[n][k]+v[k];}
 std::map<V,int> ids;edge.resize(N);
 for(int n=0;n<N;++n)for(int d=1;d<=B;++d){V v{};for(int k=0;k<3;++k)v[k]=P[n+d][k]-P[n][k];auto it=ids.find(v);if(it==ids.end())it=ids.emplace(v,static_cast<int>(ids.size())).first;edge[n].push_back(it->second);}
 for(int first=static_cast<int>(records.size());first<B;++first){
  nodes=0;maxReach=0;const auto unit=std::chrono::steady_clock::now();
  if(dfs(first,0)){std::cout<<stamp()<<" FOUND path reaching "<<N<<" first="<<first<<std::endl;return 2;}
  records.push_back({first,nodes,maxReach});
  {std::ofstream out(path+".tmp");out<<SOURCE_SHA<<' '<<B<<' '<<N<<' '<<records.size()<<'\n';for(auto r:records)out<<r.first<<' '<<r.nodes<<' '<<r.reach<<'\n';out.flush();if(!out)throw std::runtime_error("checkpoint write failed");}
  if(std::rename((path+".tmp").c_str(),path.c_str())!=0)throw std::runtime_error("checkpoint rename failed");
  const double secs=std::chrono::duration<double>(std::chrono::steady_clock::now()-unit).count();
  std::cout<<stamp()<<" completed="<<first+1<<'/'<<B<<" first="<<first<<" nodes="<<nodes<<" maxReach="<<maxReach<<" seconds="<<secs<<" nodes_per_s="<<nodes/secs<<" eta_s="<<secs*(B-first-1)<<std::endl;
 }
 uint64_t total=0;int reach=0;for(auto r:records){total+=r.nodes;reach=std::max(reach,r.reach);}
 std::cout<<stamp()<<" RESULT no path; nodes="<<total<<" maxReach="<<reach<<" vectorUniverse="<<ids.size()<<" seconds="<<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<<std::endl;
 return 0;
 }catch(const std::exception&e){std::cerr<<stamp()<<" ERROR "<<e.what()<<std::endl;return 1;}}
