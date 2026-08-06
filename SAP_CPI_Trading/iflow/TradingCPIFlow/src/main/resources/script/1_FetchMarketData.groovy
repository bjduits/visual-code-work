/*
 * Step 1: fetch crypto (CoinGecko) and stock (Yahoo Finance) market data plus
 * EUR/USD and EUR/CHF FX rates, compute momentum/volatility/score, and stash
 * the result as a JSON exchange property for the next script step.
 *
 * Reads externalized parameters (set at deploy time / Manage Integration
 * Content): CryptoFocus, StockFocus.
 *
 * Note: this calls external HTTPS endpoints directly from a Script step
 * (a well-established CPI pattern for simple GET calls to public REST APIs).
 * If your tenant's script sandbox policy blocks outbound HTTP from Groovy,
 * replace this step with proper Request-Reply steps using an HTTP Receiver
 * adapter per external call instead.
 */
import com.sap.gateway.ip.core.customdev.util.Message
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

Message processData(Message message) {
    def cryptoFocus = ((message.getProperty('CryptoFocus') ?: 'bitcoin,ethereum,chainlink,polkadot,solana') as String)
        .split(',').collect { it.trim().toLowerCase() }.findAll { it }
    def stockFocus = ((message.getProperty('StockFocus') ?: 'GME,AMC,PLTR,SOFI,BB,CLNE,SPCE') as String)
        .split(',').collect { it.trim().toUpperCase() }.findAll { it }

    def cryptoResults = fetchCrypto(cryptoFocus)
    def stockResults = stockFocus.collect { fetchStock(it) }.findAll { it != null }

    def report = [
        runAt  : new Date().format("yyyy-MM-dd'T'HH:mm:ssXXX"),
        crypto : cryptoResults,
        stocks : stockResults,
        fxRates: [EURUSD: fetchFx('EURUSD=X'), EURCHF: fetchFx('EURCHF=X')]
    ]

    def reportJson = JsonOutput.toJson(report)
    message.setProperty('MarketReportJson', reportJson)
    message.setBody(reportJson)
    return message
}

List fetchCrypto(List ids) {
    if (!ids) return []
    def url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=eur&ids=${ids.join(',')}" +
              "&order=market_cap_desc&price_change_percentage=24h,7d&sparkline=false"
    def json = httpGetJson(url)
    if (!(json instanceof List)) return []
    return json.collect { asset -> analyzeCrypto(asset) }
}

Map analyzeCrypto(asset) {
    double change24h = toDouble(asset.price_change_percentage_24h_in_currency)
    double change7d = toDouble(asset.price_change_percentage_7d_in_currency)
    double volume = toDouble(asset.total_volume)

    String momentum = 'neutral'
    if (change7d > 10 && change24h > 2) momentum = 'strong uptrend'
    else if (change7d > 3 && change24h > 0) momentum = 'moderate uptrend'
    else if (change7d < -10 && change24h < -2) momentum = 'strong downtrend'
    else if (change7d < -3 && change24h < 0) momentum = 'moderate downtrend'

    String volatility = 'low'
    if (Math.abs(change24h) > 10 || Math.abs(change7d) > 20) volatility = 'high'
    else if (Math.abs(change24h) > 5 || Math.abs(change7d) > 10) volatility = 'medium'

    String risk = 'low'
    if (volatility == 'high' || change7d < -8) risk = 'high'
    else if (volatility == 'medium' || Math.abs(change7d) > 7) risk = 'medium'

    int score = 50
    score += (int) clamp(change24h, -10.0d, 10.0d) * 2
    score += (int) clamp(change7d, -20.0d, 20.0d)
    score += (volume > 50_000_000) ? 1 : 0
    score = (int) clamp(score, 0, 100)

    return [
        symbol      : asset.symbol,
        name        : asset.name,
        currentPrice: asset.current_price,
        currency    : 'EUR',
        change24hPct: round2(change24h),
        change7dPct : round2(change7d),
        momentum    : momentum,
        volatility  : volatility,
        risk        : risk,
        score       : score,
        source      : 'CoinGecko'
    ]
}

Map fetchStock(String symbol) {
    def url = "https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?range=7d&interval=1d"
    def json
    try {
        json = httpGetJson(url)
    } catch (Exception exc) {
        return null
    }
    def result = json?.chart?.result ? json.chart.result[0] : null
    if (!result) return null

    def meta = result.meta
    def quote = result.indicators?.quote ? result.indicators.quote[0] : null
    def closes = quote?.close ? quote.close.findAll { it != null } : []

    double current = toDouble(meta?.regularMarketPrice)
    double prevClose = toDouble(meta?.chartPreviousClose ?: meta?.previousClose ?: current)
    double changePct = prevClose ? ((current - prevClose) / prevClose * 100.0) : 0.0
    double change7d = (closes.size() >= 2 && closes[0]) ? ((closes[-1] - closes[0]) / closes[0] * 100.0) : 0.0

    String momentum = 'neutral'
    if (changePct > 5 && change7d > 5) momentum = 'strong short-term bullish'
    else if (changePct > 2 && change7d > 0) momentum = 'moderate bullish'
    else if (changePct < -5 && change7d < -3) momentum = 'strong bearish'
    else if (changePct < -2 && change7d < 0) momentum = 'moderate bearish'

    int score = 50
    score += (int) clamp(changePct, -10.0d, 10.0d) * 2
    score += (int) clamp(change7d, -20.0d, 20.0d)
    score = (int) clamp(score, 0, 100)

    return [
        symbol      : meta?.symbol ?: symbol,
        name        : meta?.longName ?: meta?.shortName ?: symbol,
        currentPrice: current,
        currency    : meta?.currency ?: 'USD',
        changePct   : round2(changePct),
        change7dPct : round2(change7d),
        momentum    : momentum,
        score       : score,
        source      : 'Yahoo Finance'
    ]
}

Double fetchFx(String pair) {
    try {
        def json = httpGetJson("https://query1.finance.yahoo.com/v8/finance/chart/${pair}?range=1d&interval=1d")
        def result = json?.chart?.result ? json.chart.result[0] : null
        return result?.meta?.regularMarketPrice as Double
    } catch (Exception exc) {
        return null
    }
}

def httpGetJson(String urlString) {
    def connection = new URL(urlString).openConnection()
    connection.setRequestMethod('GET')
    connection.setRequestProperty('User-Agent', 'Mozilla/5.0 (SAP-CPI-TradingFlow)')
    connection.setConnectTimeout(15000)
    connection.setReadTimeout(15000)
    int code = connection.responseCode
    def stream = (code >= 200 && code < 300) ? connection.inputStream : connection.errorStream
    String text = stream?.getText('UTF-8')
    stream?.close()
    if (code < 200 || code >= 300) {
        throw new RuntimeException("HTTP ${code} calling ${urlString}: ${text}")
    }
    return new JsonSlurper().parseText(text)
}

double toDouble(value) {
    if (value == null) return 0.0d
    try { return (value as double) } catch (Exception exc) { return 0.0d }
}

double clamp(double value, double min, double max) {
    return Math.min(Math.max(value, min), max)
}

double round2(double value) {
    return Math.round(value * 100.0d) / 100.0d
}
