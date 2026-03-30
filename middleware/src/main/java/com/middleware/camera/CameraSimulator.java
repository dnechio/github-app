package com.middleware.camera;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Simulador de câmera Datalogic P30M para testes locais.
 *
 * Abre um ServerSocket na porta especificada e, ao receber uma conexão,
 * aguarda comandos (ex: TRIGGER) e responde com dados simulados.
 *
 * Uso: execute esta classe em uma Thread separada antes de iniciar o middleware.
 */
public class CameraSimulator implements Runnable {

    private static final Logger log = LoggerFactory.getLogger(CameraSimulator.class);

    private final String name;
    private final int port;
    private final AtomicBoolean running = new AtomicBoolean(false);

    private static final String[] SAMPLE_READINGS = {
            "1234567890;OK",
            "0987654321;OK",
            "INVALID_CODE;FAIL",
            "5556667778;OK"
    };

    private int readingIndex = 0;

    public CameraSimulator(String name, int port) {
        this.name = name;
        this.port = port;
    }

    public void start() {
        running.set(true);
        Thread t = new Thread(this, "simulator-" + name);
        t.setDaemon(true);
        t.start();
        log.info("[SIMULADOR {}] Iniciado na porta {}", name, port);
    }

    public void stop() {
        running.set(false);
    }

    @Override
    public void run() {
        try (ServerSocket serverSocket = new ServerSocket(port)) {
            while (running.get()) {
                Socket clientSocket = serverSocket.accept();
                log.info("[SIMULADOR {}] Middleware conectado.", name);
                handleClient(clientSocket);
            }
        } catch (IOException e) {
            if (running.get()) {
                log.error("[SIMULADOR {}] Erro: {}", name, e.getMessage());
            }
        }
    }

    private void handleClient(Socket clientSocket) {
        try (
            BufferedReader reader = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
            PrintWriter writer = new PrintWriter(clientSocket.getOutputStream(), true)
        ) {
            String line;
            while ((line = reader.readLine()) != null) {
                log.info("[SIMULADOR {}] Comando recebido: '{}'", name, line.trim());
                if (line.trim().equalsIgnoreCase("TRIGGER")) {
                    String response = getNextReading();
                    writer.println(response);
                    log.info("[SIMULADOR {}] Resposta enviada: '{}'", name, response);
                }
            }
        } catch (IOException e) {
            log.info("[SIMULADOR {}] Middleware desconectado.", name);
        }
    }

    private String getNextReading() {
        String reading = SAMPLE_READINGS[readingIndex % SAMPLE_READINGS.length];
        readingIndex++;
        return reading;
    }
}
