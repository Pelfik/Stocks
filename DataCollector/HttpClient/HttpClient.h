
#pragma once

#include <string>

#include <curl/curl.h>

class Curl
{
friend class HttpClient;

public:

    explicit Curl() = delete;

    static bool Init();
    static void Release();

private:

    static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp);
    static CURL* m_Curl;
};

class HttpClient
{
    public:

        std::string SendRequest(const std::string& p_Url);

    private:

            

    private:
};