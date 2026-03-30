package com.middleware.camera;

import com.middleware.config.AppConfig;
import com.middleware.model.CameraCommand;
import com.middleware.model.CameraReading;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

public class CameraManager {

    private static final Logger log = LoggerFactory.getLogger(CameraManager.class);

    private final List<CameraConnection> cameras = new ArrayList<>();

    public CameraManager(Consumer<CameraReading> onReading) {
        cameras.add(new CameraConnection(
                AppConfig.getCameraName(1),
                AppConfig.getCameraIp(1),
                AppConfig.getCameraPort(1),
                onReading
        ));
        cameras.add(new CameraConnection(
                AppConfig.getCameraName(2),
                AppConfig.getCameraIp(2),
                AppConfig.getCameraPort(2),
                onReading
        ));
    }

    public void startAll() {
        log.info("Iniciando conexoes com {} cameras...", cameras.size());
        cameras.forEach(CameraConnection::start);
    }

    public void stopAll() {
        log.info("Encerrando conexoes com cameras...");
        cameras.forEach(CameraConnection::stop);
    }

    /**
     * Envia um comando para TODAS as cameras simultaneamente.
     */
    public void broadcastCommand(CameraCommand command) {
        log.info("Broadcast de comando para {} cameras: {}", cameras.size(), command);
        cameras.forEach(cam -> cam.sendCommand(command));
    }

    public List<CameraConnection> getCameras() {
        return cameras;
    }

    public String getStatusSummary() {
        StringBuilder sb = new StringBuilder();
        for (CameraConnection cam : cameras) {
            sb.append(cam.getCameraName())
              .append(": ")
              .append(cam.isConnected() ? "CONECTADA" : "DESCONECTADA")
              .append("\n");
        }
        return sb.toString().trim();
    }
}
