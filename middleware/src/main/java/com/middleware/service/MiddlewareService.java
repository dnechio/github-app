package com.middleware.service;

import com.middleware.camera.CameraManager;
import com.middleware.erp.SankhyaClient;
import com.middleware.model.CameraCommand;
import com.middleware.model.CameraReading;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MiddlewareService {

    private static final Logger log = LoggerFactory.getLogger(MiddlewareService.class);

    private final CameraManager cameraManager;
    private final SankhyaClient sankhyaClient;

    public MiddlewareService() {
        this.sankhyaClient = new SankhyaClient();
        this.cameraManager = new CameraManager(this::handleCameraReading);
    }

    public void start() {
        log.info("Iniciando Middleware...");
        sankhyaClient.login();
        cameraManager.startAll();
        log.info("Middleware iniciado. Aguardando leituras das cameras.");
    }

    public void stop() {
        log.info("Encerrando Middleware...");
        cameraManager.stopAll();
    }

    /**
     * Recebe comando do ERP e encaminha para todas as câmeras.
     */
    public void handleErpCommand(String commandType) {
        try {
            CameraCommand.Type type = CameraCommand.Type.valueOf(commandType.toUpperCase());
            CameraCommand command = new CameraCommand(type);
            cameraManager.broadcastCommand(command);
        } catch (IllegalArgumentException e) {
            log.warn("Comando desconhecido recebido do ERP: '{}'", commandType);
        }
    }

    /**
     * Callback chamado quando uma câmera envia uma leitura.
     * Repassa os dados para o Sankhya.
     */
    private void handleCameraReading(CameraReading reading) {
        log.info("Processando leitura: {}", reading);
        boolean sent = sankhyaClient.sendCameraReading(
                reading.getCameraName(),
                reading.getReadCode(),
                reading.isSuccess()
        );
        if (!sent) {
            log.error("Falha ao encaminhar leitura ao ERP: {}", reading);
        }
    }

    public String getCameraStatus() {
        return cameraManager.getStatusSummary();
    }
}
