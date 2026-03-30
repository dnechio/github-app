package com.middleware.config;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

public class AppConfig {

    private static final Properties props = new Properties();

    static {
        try (InputStream input = AppConfig.class.getClassLoader()
                .getResourceAsStream("application.properties")) {
            if (input == null) {
                throw new RuntimeException("Arquivo application.properties não encontrado.");
            }
            props.load(input);
        } catch (IOException e) {
            throw new RuntimeException("Falha ao carregar application.properties", e);
        }
    }

    private AppConfig() {}

    public static String get(String key) {
        return props.getProperty(key);
    }

    public static int getInt(String key) {
        return Integer.parseInt(props.getProperty(key));
    }

    // --- Camera ---

    public static String getCameraIp(int cameraIndex) {
        return get("camera." + cameraIndex + ".ip");
    }

    public static int getCameraPort(int cameraIndex) {
        return getInt("camera." + cameraIndex + ".port");
    }

    public static String getCameraName(int cameraIndex) {
        return get("camera." + cameraIndex + ".name");
    }

    public static int getCameraConnectionTimeout() {
        return getInt("camera.connection.timeout.ms");
    }

    public static int getCameraReconnectInterval() {
        return getInt("camera.reconnect.interval.ms");
    }

    public static int getCameraReconnectMaxAttempts() {
        return getInt("camera.reconnect.max.attempts");
    }

    public static String getCameraDataDelimiter() {
        return get("camera.data.delimiter");
    }

    // --- Sankhya ---

    public static String getSankhyaBaseUrl() {
        return get("sankhya.base.url");
    }

    public static String getSankhyaAppKey() {
        return get("sankhya.app.key");
    }

    public static String getSankhyaUsername() {
        return get("sankhya.username");
    }

    public static String getSankhyaPassword() {
        return get("sankhya.password");
    }

    public static int getSankhyaHttpTimeout() {
        return getInt("sankhya.http.timeout.ms");
    }

    // --- Middleware ---

    public static int getMiddlewareHttpPort() {
        return getInt("middleware.http.port");
    }
}
