package com.middleware;

import com.middleware.service.MiddlewareService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Application {

    private static final Logger log = LoggerFactory.getLogger(Application.class);

    public static void main(String[] args) {
        log.info("=== Camera-ERP Middleware iniciando ===");

        MiddlewareService service = new MiddlewareService();
        service.start();

        // Garante que o middleware seja encerrado de forma limpa ao desligar a JVM
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            log.info("Sinal de desligamento recebido. Encerrando...");
            service.stop();
        }));

        // Manter a aplicacao em execucao
        try {
            Thread.currentThread().join();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
