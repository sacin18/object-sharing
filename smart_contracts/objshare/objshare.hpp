#include <eosio/eosio.hpp>
#include <eosio/asset.hpp>
#include <eosio/symbol.hpp>
#include <map>

namespace eosio {
    class [[eosio::contract]] objshare : public contract {

        public:
            enum balanceEnum {
                inprogress,
                complete
            };
            
            using contract::contract;
            objshare(name receiver, name code,  datastream<const char*> ds): contract(receiver, code, ds) {}

            [[eosio::action]]
            void transfer( name from, name to, asset quantity, std::string memo, int8_t balEnum);

            [[eosio::action]]
            void issue( name user, asset quantity );

            [[eosio::action]]
            void clearentries( name user );

            [[eosio::action]]
            void clearservs(name user);

            [[eosio::action]]
            void addservice(name to, std::string service, asset quantity);

            [[eosio::action]]
            void seekservice(name user,name from,std::string service, asset estimatedCost);

            [[eosio::action]]
            void servseeker(name user, name seeker, std::string service, asset quantity);

            [[eosio::action]]
            void abruptcomp(name from, name to, asset quantity, std::string service);
        
        private:
            const int64_t creditCut = 1000000;//100.0000
            const int64_t serviceCostCut = 100000;//10.000
            
            struct [[eosio::table]] bal_table {
                name key;
                asset confirmedBalance;
                asset debitBalance;
                asset creditBalance;
                uint64_t primary_key()const { return key.value; }
                EOSLIB_SERIALIZE(bal_table,(key)(confirmedBalance)(debitBalance)(creditBalance))
            };

            struct [[eosio::table]] serv_table {
                name key;
                std::map<std::string, asset> services;
                std::map<std::string, bool> service_usage;
                uint64_t primary_key()const { return key.value; }
                EOSLIB_SERIALIZE(serv_table, (key)(services)(service_usage))
            };

            typedef eosio::multi_index< "baltable"_n, bal_table > baltable;
            typedef eosio::multi_index< "servtable"_n, serv_table > servtable;

            void sub_balance(name user, asset quantity, balanceEnum balEnum);
            void add_balance(name user, asset quantity, name payer, balanceEnum balEnum);

    };
}