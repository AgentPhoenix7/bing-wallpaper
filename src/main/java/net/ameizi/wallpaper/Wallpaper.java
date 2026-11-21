package net.ameizi.wallpaper;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Wallpaper {

    private static final HttpClient HTTP_CLIENT = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(20))
            .followRedirects(HttpClient.Redirect.NORMAL)
            .build();
    private static final Path readmePath = Path.of("README.md");
    private static final Path wallpaperListPath = Path.of("bing-wallpaper.md");
    private static final Pattern WALLPAPER_PATTERN = Pattern.compile("^(.*?)\\s*\\|.*?\\[(.*?)\\]\\((.*?)\\)");

    // 请求API地址
    private static final String BING_API = "https://bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&nc=1618537156988&pid=hp&uhd=1&uhdwidth=3840&uhdheight=2160";
    // 最近7天
    private static final String BING_7DAYS_API = "https://bing.com/HPImageArchive.aspx?format=js&idx=%d&n=1&nc=1618537156988&pid=hp&uhd=1&uhdwidth=3840&uhdheight=2160";
    // 图片访问地址
    private static final String BING_URL = "https://bing.com%s";

    public static void main(String[] args) throws Exception {
        // 读取 wallpaper 列表
        List<Image> imageList = readWallPaperList();
        // imageList = last7Days(imageList);
        // 请求网络图片
        String resp = fetch(BING_API);
        // 解析成 Image对象
        Image image = parse(resp);
        // 在imageList下标为0的位置插入image
        imageList.add(0, image);
        // 写入bing-wallpaper.md文件
        writeToWallPaperList(imageList);
        // 写入README.md文件
        writeToReadme(imageList);
    }

    /**
     * 请求最近7天的数据
     *
     * @param imageList
     * @return
     */
    private static List<Image> last7Days(List<Image> imageList) throws IOException, InterruptedException {
        for (int i = 0; i < 8; i++) {
            String resp = fetch(String.format(BING_7DAYS_API, i));
            imageList.add(parse(resp));
        }
        return imageList;
    }

    private static String fetch(String url) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(30))
                .GET()
                .build();
        HttpResponse<String> response = HTTP_CLIENT.send(request,
                HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
        if (response.statusCode() != 200) {
            throw new IOException("Bing request failed with HTTP " + response.statusCode());
        }
        return response.body();
    }

    /**
     * 解析请求体json字符串
     *
     * @param resp
     * @return
     */
    private static Image parse(String resp) {
        JsonObject images = JsonParser.parseString(resp).getAsJsonObject()
                .getAsJsonArray("images").get(0).getAsJsonObject();

        String url = String.format(BING_URL, images.get("url").getAsString());
        int extraParameters = url.indexOf('&');
        if (extraParameters >= 0) {
            url = url.substring(0, extraParameters);
        }
        String desc = images.get("copyright").getAsString();
        String enddate = images.get("enddate").getAsString();

        LocalDate localDate = LocalDate.parse(enddate, DateTimeFormatter.BASIC_ISO_DATE);
        enddate = localDate.format(DateTimeFormatter.ISO_LOCAL_DATE);

        return new Image(enddate, desc, url);
    }

    /**
     * 解析 bing-wallpaper.md
     *
     * @return
     * @throws Exception
     */
    public static List<Image> readWallPaperList() throws Exception {
        if (!Files.exists(wallpaperListPath)) {
            return new ArrayList<>();
        }
        List<Image> imageList = new ArrayList<>();
        for (String line : Files.readAllLines(wallpaperListPath, StandardCharsets.UTF_8)) {
            Matcher matcher = WALLPAPER_PATTERN.matcher(line);
            if (matcher.find()) {
                Image image = new Image(matcher.group(1), matcher.group(2), matcher.group(3));
                imageList.add(image);
            }
        }
        return imageList;
    }

    /**
     * 写入 bing-wallpaper.md
     *
     * @param imageList
     * @throws Exception
     */
    public static void writeToWallPaperList(List<Image> imageList) throws Exception {
        StringBuilder sb = new StringBuilder("## Bing Wallpaper")
                .append(System.lineSeparator())
                .append(System.lineSeparator());
        imageList.stream().distinct().forEach(item -> sb.append(item.markdown()));
        Files.writeString(wallpaperListPath, sb.toString(), StandardCharsets.UTF_8);
    }

    /**
     * 写入 README.md
     *
     * @param imageList
     * @throws Exception
     */
    public static void writeToReadme(List<Image> imageList) throws Exception {
        Image image = imageList.get(0);
        StringBuilder sb = new StringBuilder("## Bing Wallpaper")
                .append(System.lineSeparator())
                .append(System.lineSeparator())
                .append(String.format("![%s](%s)", image.desc(), image.largeUrl()))
                .append(System.lineSeparator())
                .append(String.format("Today: [%s](%s)", image.desc(), image.url()))
                .append(System.lineSeparator())
                .append("|      |      |      |").append(System.lineSeparator())
                .append("| :--: | :--: | :--: |").append(System.lineSeparator());

        List<Image> images = imageList.stream().distinct().toList();
        int i = 1;
        for (Image item : images) {
            sb.append("|").append(item);
            if (i % 3 == 0) {
                sb.append("|").append(System.lineSeparator());
            }
            i++;
        }
        if (i % 3 != 1) {
            sb.append("|").append(System.lineSeparator());
        }
        Files.writeString(readmePath, sb.toString(), StandardCharsets.UTF_8);
    }

}
