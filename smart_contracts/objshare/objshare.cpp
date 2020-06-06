#include "objshare.hpp"
#include <string>
using namespace eosio;

void objshare::addservice(name to, std::string service, asset quantity) {
    require_auth(to);

    auto sym = quantity.symbol.code();
    check(quantity.is_valid(), "invalid quantity");
    check(quantity.amount > 0, "service cost must be positive quantity");
    check(quantity.amount <= serviceCostCut, "service cost must not be greater than serviceCostCut " + std::to_string(serviceCostCut / 10000));

    servtable ser(get_self(), to.value);
    auto iter = ser.find(to.value);
    if (iter==ser.end()) {
        ser.emplace(to, [&](auto& row) {
            row.key = to;
            row.services.insert(std::pair<std::string, asset>(service,quantity));
            row.service_usage.insert(std::pair<std::string, bool>(service, false));
        });
    } else {
        std::map<std::string, asset> tmp(((std::map<std::string, asset>)(iter->services)));
        std::map<std::string, bool> tmp2(((std::map<std::string, bool>)(iter->service_usage)));
        if (iter->services.count(service) > 0) {
            tmp[service] = quantity;
            ser.modify(iter, to, [&](auto& row) {
                row.services = tmp;
            });
        } else {
            tmp.insert(std::pair<std::string, asset>(service, quantity));
            tmp2.insert(std::pair<std::string, bool>(service, false));
            ser.modify(iter, to, [&](auto& row) {
                row.services = tmp;
                row.service_usage = tmp2;
            });
            //((std::map<std::string,asset>)(iter->services)).insert(std::pair<std::string,asset>(service,quantity));
            //((std::map<std::string, bool>)(iter->service_usage)).insert(std::pair<std::string, bool>(service, false));
        }
    }
}

void objshare::seekservice(name user, name from, std::string service, asset estimatedCost) {
    require_auth(user);
    check(is_account(from), "servicing account does not exist");
    servtable ser(get_self(), from.value);
    auto iter = ser.find(from.value);
    check(iter != ser.end(), "requested service not offered by the account");
    check(iter->services.count(service) > 0, "requested service not offered by the account");
    check(iter->services.find(service)->second == estimatedCost, "expected cost mismatch");
    check(iter->service_usage.find(service)->second == false, "requested service is begin used by another entity");
    transfer(user,from,estimatedCost,"requesting service",0);
    //((std::map<std::string, bool>)(iter->service_usage)).find(service)->second = true;
    std::map<std::string, bool> tmp2(((std::map<std::string, bool>)(iter->service_usage)));
    tmp2[service] = true;
    ser.modify(iter, from, [&](auto& row) {
        row.service_usage = tmp2;
    });
    //print("service usage value : ",((std::map<std::string, bool>)(iter->service_usage)).find(service)->second);
}

void objshare::servseeker(name user, name seeker, std::string service, asset quantity) {
    require_auth(user);
    check(is_account(seeker), "dev error :: seeker account does not exist");
    servtable ser(get_self(), user.value);
    auto iter = ser.find(user.value);
    check(iter != ser.end(), "dev error :: requested service not offered by the account");
    check(iter->services.count(service) > 0, "dev error :: requested service not offered by the account");
    check(iter->service_usage.find(service)->second == true, "dev error :: requested service is not being used by anyone");
    transfer(user, seeker, quantity, "requesting service", 1);
    //((std::map<std::string, bool>)(iter->service_usage)).find(service)->second = false;
    std::map<std::string, bool> tmp2(((std::map<std::string, bool>)(iter->service_usage)));
    tmp2[service] = false;
    ser.modify(iter, user, [&](auto& row) {
        row.service_usage = tmp2;
    });
}

void objshare::transfer( name from, name to, asset quantity, std::string memo, int8_t balEnum) {
    check( from != to, "cannot transfer to self" );
    require_auth( from );
    check( is_account( to ), "to account does not exist");
    auto sym = quantity.symbol.code();

    require_recipient( from );
    require_recipient( to );

    check( quantity.is_valid(), "invalid quantity" );
    check( quantity.amount > 0, "must transfer positive quantity" );
    check( quantity.amount <= creditCut, "must transfer amount less then the creditCut "+std::to_string(creditCut/10000));
    check( memo.size() <= 256, "memo has more than 256 bytes" );

    /*
    baltable bal(get_self(), user.value);
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
    print("Hello, ",user);
    */

   auto payer = has_auth( to ) ? to : from;
   print("quantity : ",quantity.amount);
   print(" | subtracting balance | ");
   sub_balance(from, quantity, static_cast<balanceEnum>(balEnum));
   print(" | adding balance | ");
   add_balance(to, quantity, payer, static_cast<balanceEnum>(balEnum));
}

void objshare::abruptcomp (name from, name to, asset quantity, std::string service) {
    check(from != to, "cannot transfer to self");
    require_auth(from);
    check(is_account(to), "to account does not exist");
    auto sym = quantity.symbol.code();
    
    servtable ser(get_self(), to.value);
    auto iter = ser.find(to.value);
    check(iter != ser.end(), "dev error :: requested service not offered by the account");
    check(iter->services.count(service) > 0, "dev error :: requested service not offered by the account");
    check(iter->service_usage.find(service)->second == true, "dev error :: requested service is not being used by anyone");

    require_recipient(from);
    require_recipient(to);

    check(quantity.is_valid(), "invalid quantity");
    check(quantity.amount > 0, "must transfer positive quantity");
    check(quantity.amount <= creditCut, "must transfer amount less then the creditCut " + std::to_string(creditCut / 10000));

    auto payer = has_auth(to) ? to : from;
    print("quantity : ", quantity.amount);
    print(" | subtracting balance | ");
    sub_balance(to, quantity, static_cast<balanceEnum>(1));
    print(" | adding balance | ");
    add_balance(from, quantity, payer, static_cast<balanceEnum>(1));

    //((std::map<std::string, bool>)(iter->service_usage)).find(service)->second = false;
    std::map<std::string, bool> tmp2(((std::map<std::string, bool>)(iter->service_usage)));
    tmp2[service] = false;
    ser.modify(iter, to, [&](auto& row) {
        row.service_usage = tmp2;
    });
}

void objshare::sub_balance(name user, asset quantity, balanceEnum balEnum) {
    baltable bal(get_self(), user.value);
    print("dubug :: ",quantity.symbol);
    asset creditCutAsset(creditCut,symbol(symbol_code("INR"),4));
    //const auto& from = bal.get( quantity.symbol.code().raw(), "no balance object found" );
    auto iterator = bal.find( user.value );
    if(iterator != bal.end()) {
        if(balEnum==balanceEnum::inprogress) {
            check( iterator->confirmedBalance.amount >= creditCutAsset.amount, "overdrawn balance" );
            bal.modify(iterator, user,[&]( auto& row ) {
                row.confirmedBalance -= creditCutAsset;
                row.creditBalance += creditCutAsset;
            });
        } else if(balEnum==balanceEnum::complete) {
            check( iterator->debitBalance.amount >= creditCutAsset.amount, "dev error :: overdrawn debit balance" );
            bal.modify(iterator, user,[&]( auto& row ) {
                row.debitBalance -= creditCutAsset;
                row.confirmedBalance += quantity;
            });
        }
    } else {
        check(false, "no balance object found");
    }
}

void objshare::add_balance(name user, asset quantity, name payer, balanceEnum balEnum) {
    baltable bal( get_self(), user.value );
    asset creditCutAsset(creditCut,symbol(symbol_code("INR"),4));
    auto iterator = bal.find( user.value );
    if( iterator == bal.end() ) {
        bal.emplace( payer, [&]( auto& row ){
            row.key = user;
            if(balEnum==balanceEnum::inprogress) {
                row.debitBalance = creditCutAsset;
            } 
            row.confirmedBalance.amount = 0.0000;
            row.creditBalance.amount = 0.0000;
            row.confirmedBalance.symbol = quantity.symbol;
            row.debitBalance.symbol = quantity.symbol;
            row.creditBalance.symbol = quantity.symbol;
        });
    } else {
        if(balEnum==balanceEnum::inprogress) {
            bal.modify(iterator, user, [&]( auto& row ) {
                row.debitBalance += creditCutAsset;
            });
        } else if(balEnum==balanceEnum::complete) {
            bal.modify(iterator, user, [&]( auto& row ) {
                row.creditBalance-=creditCutAsset;
                row.confirmedBalance+=creditCutAsset-quantity;
                if(row.creditBalance.amount<0) {
                    row.creditBalance.amount = 0;
                    check(false,"dev error :: completed-creditBalance at customer <0 : unfair profit condition");
                }
            });
        }
    }
}

void objshare::issue( name user, asset quantity ) {
    require_auth( user );
    auto sym = quantity.symbol.code();

    check( quantity.is_valid(), "invalid quantity" );
    check( quantity.amount > 0, "must transfer positive quantity" );

    baltable bal(get_self(), user.value);
    auto iterator = bal.find(user.value);
    if( iterator == bal.end() )
    {
        std::string sym = "INR";
        symbol_code symbolcode(sym);
        symbol symbolvalue(symbolcode,4);
        bal.emplace(user, [&]( auto& row ) {
            row.key = user;
            row.confirmedBalance = quantity;
            row.debitBalance.amount = 0;
            row.creditBalance.amount = 0;
            row.debitBalance.symbol = quantity.symbol;
            row.creditBalance.symbol = quantity.symbol;
        });
    } else {
        bal.modify(iterator, user, [&](auto& row) {
            row.confirmedBalance += quantity;
        });
    }

}

void objshare::clearentries(name user) {
    baltable bal(get_self(), user.value);
    auto iterator = bal.find(user.value);
    while(iterator != bal.end()) {
        bal.erase(iterator);
        iterator = bal.find(user.value);
    }
}

void objshare::clearservs(name user) {
    servtable ser(get_self(), user.value);
    auto iterator = ser.find(user.value);
    while (iterator != ser.end()) {
        ser.erase(iterator);
        iterator = ser.find(user.value);
    }
}