package com.middleware.erp;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.middleware.config.AppConfig;
import okhttp3.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

public class SankhyaClient {

    private static final Logger log = LoggerFactory.getLogger(SankhyaClient.class);
    private static final MediaType JSON = MediaType.parse("application/json; charset=utf-8");

    private final OkHttpClient httpClient;
    private final Gson gson = new Gson();
    private final String baseUrl;

    private String sessionId;

    public SankhyaClient() {
        int timeout = AppConfig.getSankhyaHttpTimeout();
        this.baseUrl = AppConfig.getSankhyaBaseUrl();
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(timeout, TimeUnit.MILLISECONDS)
                .readTimeout(timeout, TimeUnit.MILLISECONDS)
                .writeTimeout(timeout, TimeUnit.MILLISECONDS)
                .build();
    }

    /**
     * Realiza login no Sankhya e armazena o JSESSIONID para uso nas demais chamadas.
     */
    public boolean login() {
        String url = baseUrl + "/service.sbr?service=MobileLoginSP.login&outputType=json";

        JsonObject body = new JsonObject();
        body.addProperty("NOMUSU", AppConfig.getSankhyaUsername());
        body.addProperty("PWD", AppConfig.getSankhyaPassword());
        body.addProperty("APPKEY", AppConfig.getSankhyaAppKey());

        try {
            String responseBody = post(url, body.toString());
            JsonObject response = gson.fromJson(responseBody, JsonObject.class);

            // Extrai o JSESSIONID da resposta
            sessionId = response
                    .getAsJsonObject("responseBody")
                    .getAsJsonObject("jsessionid")
                    .get("$").getAsString();

            log.info("Login Sankhya realizado com sucesso. Session: {}", sessionId);
            return true;
        } catch (Exception e) {
            log.error("Falha no login do Sankhya: {}", e.getMessage());
            return false;
        }
    }

    /**
     * Envia a leitura de uma câmera para o Sankhya.
     * O nome da entidade e dos campos deve ser ajustado conforme o dicionário de dados do cliente.
     */
    public boolean sendCameraReading(String cameraName, String readCode, boolean success) {
        if (sessionId == null) {
            log.warn("Tentativa de envio sem sessao ativa. Realizando login...");
            if (!login()) return false;
        }

        String url = baseUrl + "/service.sbr?service=DatasetSP.saveRecord&outputType=json&mgeSession=" + sessionId;

        JsonObject field = new JsonObject();
        // TODO: ajustar os nomes dos campos conforme dicionario de dados do Sankhya
        field.addProperty("CAMERA", cameraName);
        field.addProperty("CODBARRA", readCode);
        field.addProperty("STATUS", success ? "OK" : "FAIL");

        JsonObject dataSet = new JsonObject();
        dataSet.addProperty("rootEntity", "AD_LEITURACAMERA"); // TODO: confirmar nome da entidade
        dataSet.add("dataRow", field);

        JsonObject requestBody = new JsonObject();
        requestBody.add("dataSet", dataSet);

        try {
            String response = post(url, requestBody.toString());
            log.info("Leitura enviada ao Sankhya. Camera: {}, Codigo: {}, Status: {}", cameraName, readCode, success);
            log.debug("Resposta Sankhya: {}", response);
            return true;
        } catch (Exception e) {
            log.error("Falha ao enviar leitura ao Sankhya: {}", e.getMessage());
            return false;
        }
    }

    private String post(String url, String jsonBody) throws IOException {
        RequestBody body = RequestBody.create(jsonBody, JSON);
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException("Resposta HTTP inesperada: " + response.code());
            }
            return response.body() != null ? response.body().string() : "";
        }
    }
}
