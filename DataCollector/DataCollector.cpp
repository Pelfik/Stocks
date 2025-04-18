
#include <iostream>
#include <string>

#include "HttpClient/HttpClient.h"

#include "simdjson.h"

/*struct Car
{
    std::string make;
    std::string model;
    int64_t year;
    std::vector<double> tire_pressure;
};

#if !SIMDJSON_SUPPORTS_DESERIALIZATION
// The code is unnecessary with C++20:
template <>
simdjson_inline simdjson::simdjson_result<std::vector<double>>
simdjson::ondemand::value::get() noexcept
{
    simdjson::ondemand::array array;
    auto error = get_array().get(array);
    if (error) { return error; }
    std::vector<double> vec;
    for (auto v : array)
    {
        double val;
        error = v.get_double().get(val);
        if (error) { return error; }
        vec.push_back(val);
    }
    return vec;
}
#endif

template <>
simdjson_inline simdjson::simdjson_result<Car> simdjson::ondemand::value::get() noexcept {
    simdjson::ondemand::object obj;
    auto error = get_object().get(obj);
    if (error) { return error; }
    Car car;
    if ((error = obj["make"].get_string(car.make))) { return error; }
    if ((error = obj["model"].get_string(car.model))) { return error; }
    if ((error = obj["year"].get_int64().get(car.year))) { return error; }
    if ((error = obj["tire_pressure"].get<std::vector<double>>().get(car.tire_pressure))) { return error; }
    return car;
}*/

struct MetaData
{
    std::string Information;
    std::string Symbol;
    std::string LastRefreshed;
    std::string OutputSize;
    std::string TimeZone;
};

template <>
simdjson_inline simdjson::simdjson_result<MetaData> simdjson::ondemand::value::get() noexcept
{
    simdjson::ondemand::object obj;
    auto error = get_object().get(obj);
    if (error)
        return error;

    MetaData l_MetaData;

    if ((error = obj["1. Information"].get_string(l_MetaData.Information))) { return error; }
    if ((error = obj["2. Symbol"].get_string(l_MetaData.Symbol))) { return error; }
    if ((error = obj["3. Last Refreshed"].get_string(l_MetaData.LastRefreshed))) { return error; }
    if ((error = obj["4. Output Size"].get_string(l_MetaData.OutputSize))) { return error; }
    if ((error = obj["5. Time Zone"].get_string(l_MetaData.TimeZone))) { return error; }

    return l_MetaData;
}

 /*   "Meta Data" : {
    "1. Information": "Daily Prices (open, high, low, close) and Volumes",
        "2. Symbol" : "BARC.LON",
        "3. Last Refreshed" : "2025-03-12",
        "4. Output Size" : "Compact",
        "5. Time Zone" : "US/Eastern"*/
void recursive_print_json(simdjson::ondemand::value element)
{
  bool add_comma;
  switch (element.type()) {
  case simdjson::ondemand::json_type::array:
    std::cout << "[";
    add_comma = false;
    for (auto child : element.get_array()) {
      if (add_comma) {
          std::cout << ",";
      }
      // We need the call to value() to get
      // an ondemand::value type.
      recursive_print_json(child.value());
      add_comma = true;
    }
    std::cout << "]";
    break;
  case simdjson::ondemand::json_type::object:
      std::cout << "{";
    add_comma = false;
    for (auto field : element.get_object()) {
      if (add_comma) {
          std::cout << ",";
      }
      // key() returns the key as it appears in the raw
      // JSON document, if we want the unescaped key,
      // we should do field.unescaped_key().
      // We could also use field.escaped_key() if we want
      // a std::string_view instance, but we do not need
      // escaping.
      std::cout << "\"" << field.key() << "\": ";
      recursive_print_json(field.value());
      add_comma = true;
    }
    std::cout << "}\n";
    break;
  case simdjson::ondemand::json_type::number:
    // assume it fits in a double
      std::cout << element.get_double();
    break;
  case simdjson::ondemand::json_type::string:
    // get_string() would return escaped string, but
    // we are happy with unescaped string.
      std::cout << "\"" << element.get_raw_json_string() << "\"";
    break;
  case simdjson::ondemand::json_type::boolean:
      std::cout << element.get_bool();
    break;
  case simdjson::ondemand::json_type::null:
    // We check that the value is indeed null
    // otherwise: an error is thrown.
    if (element.is_null()) {
        std::cout << "null";
    }
    break;
  }
}

int main()
{
    if (!Curl::Init())
    {
        printf("Cannot initialise curl.");
    }

    std::string url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=BARC.LON&interval=5min&outputsize=compact&apikey=apikey";

    HttpClient client;
    std::string result = client.SendRequest(url);

    printf("Result: %s", result.c_str());

    //simdjson::padded_string json = simdjson::padded_string::load("twitter.json");
    simdjson::ondemand::parser parser;
    simdjson::ondemand::document tweets = parser.iterate(result);
    simdjson::ondemand::value val = tweets;
    
    //auto type = val.type();
    //std::string_view s = val.raw_json().value();
    //std::string ss(s);


    for (auto field : val.get_object())
    {
        std::string k(field.value().get_string().value());
        std::cout << "\"" << field.key() << "\": ";
        MetaData d(field.value());
        //recursive_print_json(field.value());
        std::cout << "\"" << field.key() << "\": ";
    }

    recursive_print_json(val);

    return 0;
}
