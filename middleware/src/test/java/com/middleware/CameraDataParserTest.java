package com.middleware;

import com.middleware.camera.CameraDataParser;
import com.middleware.model.CameraReading;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class CameraDataParserTest {

    @Test
    void deveParsearLeituraOK() {
        CameraReading reading = CameraDataParser.parse("Camera-01", "1234567890;OK");
        assertEquals("1234567890", reading.getReadCode());
        assertTrue(reading.isSuccess());
    }

    @Test
    void deveParsearLeituraFAIL() {
        CameraReading reading = CameraDataParser.parse("Camera-01", "INVALID_CODE;FAIL");
        assertEquals("INVALID_CODE", reading.getReadCode());
        assertFalse(reading.isSuccess());
    }

    @Test
    void deveRetornarFalhaSemDelimitador() {
        CameraReading reading = CameraDataParser.parse("Camera-01", "DADO_SEM_DELIMITADOR");
        assertFalse(reading.isSuccess());
        assertEquals("DADO_SEM_DELIMITADOR", reading.getRawData());
    }

    @Test
    void deveIgnorarEspacosExtras() {
        CameraReading reading = CameraDataParser.parse("Camera-01", " ABC123 ; OK ");
        assertEquals("ABC123", reading.getReadCode());
        assertTrue(reading.isSuccess());
    }
}
