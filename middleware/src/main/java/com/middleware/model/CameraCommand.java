package com.middleware.model;

public class CameraCommand {

    public enum Type {
        TRIGGER,
        STATUS
    }

    private final Type type;
    private final String rawCommand;

    public CameraCommand(Type type) {
        this.type = type;
        this.rawCommand = type.name() + "\r\n";
    }

    public CameraCommand(Type type, String rawCommand) {
        this.type = type;
        this.rawCommand = rawCommand;
    }

    public Type getType() { return type; }

    public byte[] toBytes() {
        return rawCommand.getBytes();
    }

    @Override
    public String toString() {
        return "CameraCommand{type=" + type + ", raw='" + rawCommand.trim() + "'}";
    }
}
