package net.ameizi.wallpaper;

import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

class WallpaperTest {

    private Image parse(String json) throws Exception {
        var method = Wallpaper.class.getDeclaredMethod("parse", String.class);
        method.setAccessible(true);
        try {
            return (Image) method.invoke(null, json);
        } catch (InvocationTargetException exception) {
            throw (Exception) exception.getCause();
        }
    }

    @Test
    void parsesBingResponseWithoutChangingDateDescriptionOrDownloadUrl() throws Exception {
        Image result = parse("""
                {"images":[{"url":"/th?id=OHR.Example_UHD.jpg&rf=example&pid=hp",
                "enddate":"20261121","copyright":"Côte d’Azur 日本 © Photographer"}]}
                """);
        assertEquals(new Image("2026-11-21", "Côte d’Azur 日本 © Photographer",
                "https://bing.com/th?id=OHR.Example_UHD.jpg"), result);
    }

    @Test
    void acceptsImageUrlWithoutExtraQueryParameters() throws Exception {
        Image result = parse("""
                {"images":[{"url":"/th?id=OHR.Example_UHD.jpg",
                "enddate":"20261121","copyright":"Example"}]}
                """);
        assertEquals("https://bing.com/th?id=OHR.Example_UHD.jpg", result.url());
    }

    @Test
    void rejectsEmptyImageList() {
        assertThrows(Exception.class, () -> parse("{\"images\":[]}"));
    }

    @Test
    void rejectsMalformedJson() {
        assertThrows(Exception.class, () -> parse("not JSON"));
    }

    private String fetch(String uri) throws Exception {
        var method = Wallpaper.class.getDeclaredMethod("fetch", String.class);
        method.setAccessible(true);
        try {
            return (String) method.invoke(null, uri);
        } catch (InvocationTargetException exception) {
            throw (Exception) exception.getCause();
        }
    }

    @Test
    void fetchesUtf8ResponseAndFollowsRedirects() throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        byte[] expected = "{\"copyright\":\"日本 ©\"}".getBytes(StandardCharsets.UTF_8);
        server.createContext("/image", exchange -> {
            exchange.sendResponseHeaders(200, expected.length);
            try (var output = exchange.getResponseBody()) {
                output.write(expected);
            }
        });
        server.createContext("/redirect", exchange -> {
            exchange.getResponseHeaders().set("Location", "/image");
            exchange.sendResponseHeaders(302, -1);
            exchange.close();
        });
        server.start();
        try {
            assertEquals(new String(expected, StandardCharsets.UTF_8),
                    fetch("http://127.0.0.1:" + server.getAddress().getPort() + "/redirect"));
        } finally {
            server.stop(0);
        }
    }

    @Test
    void rejectsHttpErrorBeforeParsingTheResponse() throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/unavailable", exchange -> {
            exchange.sendResponseHeaders(503, -1);
            exchange.close();
        });
        server.start();
        try {
            IOException error = assertThrows(IOException.class,
                    () -> fetch("http://127.0.0.1:" + server.getAddress().getPort() + "/unavailable"));
            assertTrue(error.getMessage().contains("503"));
        } finally {
            server.stop(0);
        }
    }
}
