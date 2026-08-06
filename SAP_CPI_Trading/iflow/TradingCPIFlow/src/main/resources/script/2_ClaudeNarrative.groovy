/*
 * Step 2: build a Dutch-language advisor prompt from the market report
 * produced by step 1, call the Anthropic Claude Messages API, and stash the
 * narrative text as an exchange property for the PDF-building step.
 *
 * The Anthropic API key is read from a CPI Security Material "User
 * Credentials" artifact named "Anthropic_API_Key" (create this under
 * Monitor > Security Material after importing the flow; the password field
 * holds the API key, the username field can be anything, e.g. "anthropic").
 *
 * Reads externalized parameter: ClaudeModel (defaults to claude-opus-4-8).
 */
import com.sap.gateway.ip.core.customdev.util.Message
import com.sap.it.api.ITApiFactory
import com.sap.it.api.securestore.SecureStoreService
import com.sap.it.api.securestore.UserCredential
import groovy.json.JsonOutput
import groovy.json.JsonSlurper

Message processData(Message message) {
    def reportJson = message.getProperty('MarketReportJson') as String
    def report = new JsonSlurper().parseText(reportJson)
    def model = (message.getProperty('ClaudeModel') ?: 'claude-opus-4-8') as String

    def secureStoreService = ITApiFactory.getApi(SecureStoreService.class, null)
    UserCredential credential = secureStoreService?.getUserCredential('Anthropic_API_Key')
    if (credential == null) {
        throw new IllegalStateException(
            "Security Material 'Anthropic_API_Key' not found. Create a User " +
            "Credentials artifact with this exact name under Monitor > Security " +
            "Material, with the Anthropic API key stored as the password."
        )
    }
    String apiKey = new String(credential.getPassword())

    def prompt = buildPrompt(report)
    def narrative = callClaude(prompt, apiKey, model)

    message.setProperty('Narrative', narrative)
    message.setProperty('GeneratedAt', new Date().format('yyyy-MM-dd HH:mm'))
    return message
}

String buildPrompt(report) {
    def lines = []
    lines << (
        "Je bent een warme, vriendelijke beleggingsadviseur die schrijft voor een " +
        "particuliere belegger. De belegger houdt zijn geld voornamelijk in EUR aan, " +
        "met een deel in Zwitserse frank (CHF) als reserve. Schrijf in het Nederlands, " +
        "in een bemoedigende, prettig leesbare stijl (platte tekst, geen kopjes, geen " +
        "markdown, geen opsommingstekens), verdeeld in 5-6 korte alinea's die het " +
        "volgende behandelen: de algemene marktstemming vandaag, de beste kansen " +
        "onder de hieronder genoemde aandelen en cryptovaluta en waarom, wat te " +
        "vermijden en waarom (risicofactoren), de rol van de wisselkoersen EUR/USD " +
        "en EUR/CHF voor deze posities (gebruik de cijfers hieronder, verzin geen " +
        "andere koersen), en een vriendelijke afsluiting die benadrukt dat dit " +
        "educatief onderzoek is, geen financieel advies, en dat de lezer alles zelf " +
        "moet verifieren.\n\nMarktdata:"
    )
    (report.crypto ?: []).each { a ->
        lines << "- ${a.symbol} (${a.name}, Crypto): prijs=${a.currentPrice} ${a.currency} " +
                 "24u=${a.change24hPct}% 7d=${a.change7dPct}% momentum=${a.momentum} " +
                 "risico=${a.risk} score=${a.score}"
    }
    (report.stocks ?: []).each { a ->
        lines << "- ${a.symbol} (${a.name}, Aandeel): prijs=${a.currentPrice} ${a.currency} " +
                 "1d=${a.changePct}% 7d=${a.change7dPct}% momentum=${a.momentum} score=${a.score}"
    }
    lines << "\nWisselkoersen: 1 EUR ≈ ${report.fxRates?.EURUSD} USD, 1 EUR ≈ ${report.fxRates?.EURCHF} CHF"
    return lines.join('\n')
}

String callClaude(String prompt, String apiKey, String model) {
    def connection = new URL('https://api.anthropic.com/v1/messages').openConnection()
    connection.setRequestMethod('POST')
    connection.setDoOutput(true)
    connection.setConnectTimeout(30000)
    connection.setReadTimeout(60000)
    connection.setRequestProperty('Content-Type', 'application/json')
    connection.setRequestProperty('x-api-key', apiKey)
    connection.setRequestProperty('anthropic-version', '2023-06-01')

    def payload = JsonOutput.toJson([
        model     : model,
        max_tokens: 2000,
        system    : 'Je bent een vriendelijke, toegankelijke beleggingsadviseur die in het ' +
                    'Nederlands schrijft. Dit is educatief onderzoek, geen financieel advies.',
        messages  : [[role: 'user', content: prompt]]
    ])

    connection.outputStream.withWriter('UTF-8') { it << payload }

    int code = connection.responseCode
    def stream = (code >= 200 && code < 300) ? connection.inputStream : connection.errorStream
    String text = stream?.getText('UTF-8')
    stream?.close()
    if (code < 200 || code >= 300) {
        throw new RuntimeException("Claude API error ${code}: ${text}")
    }

    def json = new JsonSlurper().parseText(text)
    return (json.content ?: []).findAll { it.type == 'text' }.collect { it.text }.join('').trim()
}
