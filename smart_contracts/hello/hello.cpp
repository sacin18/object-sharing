#include <eosio/eosio.hpp>
#include <eosio/asset.hpp>
#include <eosio/symbol.hpp>
using namespace eosio;

class [[eosio::contract]] hello : public contract {
    public:
        using contract::contract;
        hello(name receiver, name code,  datastream<const char*> ds): contract(receiver, code, ds) {}

        [[eosio::action]]
        void hi( name user ) {
            require_auth( user );
            baltable bal(get_self(), get_first_receiver().value);
            auto iterator = bal.find(user.value);
            if( iterator == bal.end() )
            {
                std::string sym = "INR";
                symbol_code symbolcode(sym);
                symbol symbolvalue(symbolcode,4);
                bal.emplace(user, [&]( auto& row ) {
                    row.key = user;
                    row.confirmedBalance.amount = 1.0000;
                    row.debitBalance.amount = 2.0000;
                    row.creditBalance.amount = 3.0000;
                    row.confirmedBalance.symbol = symbolvalue;
                    row.debitBalance.symbol = symbolvalue;
                    row.creditBalance.symbol = symbolvalue;
                });
            } else {
                print("some data has been entered");
                print(" ",(iterator->confirmedBalance).amount," ");
                bal.erase(iterator);
            }
            /*
            iterator = bal.begin();
            while(iterator!=bal.end()) {
                if((iterator->confirmedBalance).amount==0.00) {
                    print("found");
                    bal.erase(iterator);
                    break;
                }
            }
            */
            print("Hello, ",user);
        }

        
    
    private:

        struct [[eosio::table]] bal_table {
            name key;
            asset confirmedBalance;
            asset debitBalance;
            asset creditBalance;  
            uint64_t primary_key()const { return key.value; }
            EOSLIB_SERIALIZE(bal_table,(key)(confirmedBalance)(debitBalance)(creditBalance))
         };

         typedef eosio::multi_index< "baltable"_n, bal_table > baltable;

};