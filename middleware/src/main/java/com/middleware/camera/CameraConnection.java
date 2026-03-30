package com.middleware.camera;

import com.middleware.config.AppConfig;
import com.middleware.model.CameraCommand;
import com.middleware.model.CameraReading;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;

public class CameraConnection implements Runnable {

    private static final Logger log = LoggerFactory.getLogger(CameraConnection.class);

    private final String cameraName;
    private final String ip;
    private final int port;
    private final Consumer<CameraReading> onReading;

    private Socket socket;
    private PrintWriter writer;
    private final AtomicBoolean running = new AtomicBoolean(false);
    private final AtomicBoolean connected = new AtomicBoolean(false);

    public CameraConnection(String cameraName, String ip, int port, Consumer<CameraReading> onReading) {
        this.cameraName = cameraName;
        this.ip = ip;
        this.port = port;
        this.onReading = onReading;
    }

    public void start() {
        running.set(true);
        Thread thread = new Thread(this, "camera-" + cameraName);
        thread.setDaemon(true);
        thread.start();
    }

    public void stop() {
        running.set(false);
        closeSocket();
    }

    @Override
    public void run() {
        int attempts = 0;
        int maxAttempts = AppConfig.getCameraReconnectMaxAttempts();

        while (running.get() && attempts < maxAttempts) {
            try {
                connect();
                attempts = 0;
                listenForData();
            } catch (IOException e) {
                connected.set(false);
                attempts++;
                log.warn("[{}] Conexao perdida (tentativa {}/{}): {}",
                        cameraName, attempts, maxAttempts, e.getMessage());
                sleep(AppConfig.getCameraReconnectInterval());
            }
        }

        if (attempts >= maxAttempts) {
            log.error("[{}] Numero maximo de tentativas de reconexao atingido. Encerrando.", cameraName);
        }
    }

    private void connect() throws IOException {
        closeSocket();
        log.info("[{}] Conectando em {}:{}...", cameraName, ip, port);
        socket = new Socket();
        socket.connect(
                new java.net.InetSocketAddress(ip, port),
                AppConfig.getCameraConnectionTimeout()
        );
        socket.setSoTimeout(0); // sem timeout de leitura (conexao persistente)
        writer = new PrintWriter(new OutputStreamWriter(socket.getOutputStream()), true);
        connected.set(true);
        log.info("[{}] Conectado com sucesso.", cameraName);
    }

    private void listenForData() throws IOException {
        BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream()));
        String line;
        while (running.get() && (line = reader.readLine()) != null) {
            if (!line.isBlank()) {
                CameraReading reading = CameraDataParser.parse(cameraName, line);
                log.info("[{}] Leitura recebida: {}", cameraName, reading);
                onReading.accept(reading);
            }
        }
    }

    public void sendCommand(CameraCommand command) {
        if (!connected.get() || writer == null) {
            log.warn("[{}] Tentativa de enviar comando sem conexao ativa: {}", cameraName, command);
            return;
        }
        writer.print(new String(command.toBytes()));
        writer.flush();
        log.info("[{}] Comando enviado: {}", cameraName, command);
    }

    public boolean isConnected() {
        return connected.get() && socket != null && socket.isConnected() && !socket.isClosed();
    }

    public String getCameraName() {
        return cameraName;
    }

    private void closeSocket() {
        try {
            if (socket != null && !socket.isClosed()) {
                socket.close();
            }
        } catch (IOException e) {
            log.debug("[{}] Erro ao fechar socket: {}", cameraName, e.getMessage());
        } finally {
            connected.set(false);
        }
    }

    private void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
