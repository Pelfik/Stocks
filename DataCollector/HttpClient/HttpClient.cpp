
#include "HttpClient.h"

CURL* Curl::m_Curl;

bool Curl::Init()
{
    curl_global_init(CURL_GLOBAL_DEFAULT);
    m_Curl = curl_easy_init();
    return m_Curl != nullptr;
}

void Curl::Release()
{
    curl_global_cleanup();
    m_Curl = nullptr;
}

size_t Curl::WriteCallback(void* contents, size_t size, size_t nmemb, void* userp)
{
    size_t total_size = size * nmemb;
    std::string* response = static_cast<std::string*>(userp);
    response->append(static_cast<char*>(contents), total_size);
    return total_size;
}

std::string HttpClient::HttpClient::SendRequest(const std::string& p_Url)
{
    if (Curl::m_Curl == nullptr)
        return "";

    CURLcode res;
    std::string response_data;

    curl_easy_setopt(Curl::m_Curl, CURLOPT_URL, p_Url.c_str());
    curl_easy_setopt(Curl::m_Curl, CURLOPT_WRITEFUNCTION, Curl::WriteCallback);
    curl_easy_setopt(Curl::m_Curl, CURLOPT_WRITEDATA, &response_data);

    res = curl_easy_perform(Curl::m_Curl);

    curl_easy_cleanup(Curl::m_Curl);
   
    return response_data;
}