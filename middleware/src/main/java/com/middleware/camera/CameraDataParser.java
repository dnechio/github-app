package com.middleware.camera;

import com.middleware.config.AppConfig;
import com.middleware.model.CameraReading;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CameraDataParser {

    private static final Logger log = LoggerFactory.getLogger(CameraDataParser.class);

    private CameraDataParser() {}

    /**
     * Converte a string bruta recebida da câmera em um objeto CameraReading.
     *
     * Formato esperado (configurado no IMPACT VPM):
     *   CODIGO_LIDO;OK
     *   CODIGO_LIDO;FAIL
     *
     * Exemplo: "1234567890;OK"
     */
    public static CameraReading parse(String cameraName, String rawData) {
        String delimiter = AppConfig.getCameraDataDelimiter();
        String[] parts = rawData.trim().split(delimiter);

        if (parts.length < 2) {
            log.warn("[{}] Formato de dado inesperado: '{}'", cameraName, rawData);
            return new CameraReading(cameraName, rawData, rawData, false);
        }

        String readCode = parts[0].trim();
        boolean success = "OK".equalsIgnoreCase(parts[1].trim());

        return new CameraReading(cameraName, rawData, readCode, success);
    }
}
