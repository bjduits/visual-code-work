/*
 * Step 3: render the market report + Claude narrative as a PDF, entirely by
 * hand-writing PDF 1.4 syntax (no external library). SAP CPI's Script step
 * sandbox cannot load a full PDF library (e.g. iText/PDFBox) unless one is
 * uploaded as an "Imported Archive" resource on the iFlow — this script
 * avoids that dependency by building a minimal, valid PDF directly.
 *
 * Layout is intentionally simple (single monospace font, left-aligned text,
 * word-wrapped by character count) to keep the byte-level construction
 * (content streams, object offsets, xref table) reliable without a real
 * font-metrics engine. If you later add a PDF library as a resource archive,
 * this whole script can be replaced with a few lines using that library.
 *
 * Sets the message body to the PDF bytes, ready for the Mail Receiver step.
 */
import com.sap.gateway.ip.core.customdev.util.Message
import groovy.json.JsonSlurper

Message processData(Message message) {
    def reportJson = message.getProperty('MarketReportJson') as String
    def report = new JsonSlurper().parseText(reportJson)
    def narrative = (message.getProperty('Narrative') ?: '') as String
    def generatedAt = (message.getProperty('GeneratedAt') ?: new Date().format('yyyy-MM-dd HH:mm')) as String

    def lines = []
    lines << [type: 'title', text: 'SAP CPI Trading Advisor Report']
    lines << [type: 'meta', text: "Gegenereerd op ${generatedAt} - Educatief onderzoek, geen financieel advies"]
    lines << [type: 'blank', text: '']

    lines << [type: 'heading', text: 'Marktoverzicht']
    (report.crypto ?: []).each { a ->
        wrapText(
            "${(a.symbol ?: '').toString().toUpperCase()} (${a.name}) [Crypto] prijs=${a.currentPrice} " +
            "${a.currency} 24u=${a.change24hPct}% 7d=${a.change7dPct}% momentum=${a.momentum} " +
            "risico=${a.risk} score=${a.score}", 95
        ).each { lines << [type: 'body', text: it] }
    }
    (report.stocks ?: []).each { a ->
        wrapText(
            "${a.symbol} (${a.name}) [Aandeel] prijs=${a.currentPrice} ${a.currency} " +
            "1d=${a.changePct}% 7d=${a.change7dPct}% momentum=${a.momentum} score=${a.score}", 95
        ).each { lines << [type: 'body', text: it] }
    }
    lines << [type: 'blank', text: '']

    lines << [type: 'heading', text: 'Vooruitzicht']
    (narrative ? narrative.split('\n\n') : []).each { para ->
        if (para?.trim()) {
            wrapText(para.trim(), 95).each { lines << [type: 'body', text: it] }
            lines << [type: 'blank', text: '']
        }
    }

    lines << [type: 'heading', text: 'Wisselkoersen']
    lines << [type: 'body', text: "1 EUR ~ ${report.fxRates?.EURUSD} USD, 1 EUR ~ ${report.fxRates?.EURCHF} CHF"]
    lines << [type: 'blank', text: '']

    wrapText(
        'Dit rapport is automatisch gegenereerd door een SAP Cloud Integration flow op basis van ' +
        'publieke marktdata en een AI-samenvatting, uitsluitend voor educatieve doeleinden. Dit is ' +
        'geen financieel advies. Controleer altijd actuele prijzen en platformbeschikbaarheid voordat u handelt.',
        95
    ).each { lines << [type: 'small', text: it] }

    byte[] pdfBytes = buildPdf(lines)
    message.setBody(pdfBytes)
    message.setProperty('PdfFileName', "trading_cpi_report_${new Date().format('yyyy-MM-dd')}.pdf")
    message.setHeader('Content-Type', 'application/pdf')
    return message
}

List<String> wrapText(String text, int maxChars) {
    def words = text.split(/\s+/)
    def wrapped = []
    def current = new StringBuilder()
    words.each { w ->
        if (current.length() > 0 && current.length() + w.length() + 1 > maxChars) {
            wrapped << current.toString()
            current = new StringBuilder()
        }
        if (current.length() > 0) current << ' '
        current << w
    }
    if (current.length() > 0) wrapped << current.toString()
    return wrapped ?: ['']
}

String escapePdfText(String text) {
    def safe = (text ?: '').collect { ch ->
        int cp = (int) ch.charAt(0)
        cp <= 255 ? ch : '?'
    }.join('')
    return safe.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
}

byte[] buildPdf(List lines) {
    double pageWidth = 595.28d
    double pageHeight = 841.89d
    double marginLeft = 45d
    double marginTop = 45d
    double marginBottom = 45d
    double bodySize = 9.5d
    double titleSize = 16d
    double headingSize = 12d
    double smallSize = 7.5d
    double lineHeight = bodySize * 1.35d

    int linesPerPage = (int) Math.floor((pageHeight - marginTop - marginBottom) / lineHeight) - 2
    if (linesPerPage < 10) linesPerPage = 30

    def pages = lines.collate(linesPerPage)
    if (pages.isEmpty()) pages = [[]]

    def out = new ByteArrayOutputStream()
    def offsets = [:]

    Closure write = { String s -> out.write(s.getBytes('ISO-8859-1')) }
    Closure writeObjStart = { int num -> offsets[num] = out.size(); write("${num} 0 obj\n") }
    Closure writeObjEnd = { write("endobj\n") }

    int fontRegular = 1
    int fontBold = 2
    int catalogNum = 3
    int pagesNum = 4
    int firstPageNum = 5
    int firstContentNum = firstPageNum + pages.size()
    int totalObjects = firstContentNum + pages.size() - 1

    write("%PDF-1.4\n")

    writeObjStart(fontRegular)
    write("<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>\n")
    writeObjEnd()

    writeObjStart(fontBold)
    write("<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold /Encoding /WinAnsiEncoding >>\n")
    writeObjEnd()

    def pageObjNums = (0..<pages.size()).collect { firstPageNum + it }
    def contentObjNums = (0..<pages.size()).collect { firstContentNum + it }

    writeObjStart(catalogNum)
    write("<< /Type /Catalog /Pages ${pagesNum} 0 R >>\n")
    writeObjEnd()

    writeObjStart(pagesNum)
    write("<< /Type /Pages /Kids [${pageObjNums.collect { it + ' 0 R' }.join(' ')}] /Count ${pages.size()} >>\n")
    writeObjEnd()

    pages.eachWithIndex { pageLines, pageIndex ->
        int pageNum = pageObjNums[pageIndex]
        int contentNum = contentObjNums[pageIndex]

        writeObjStart(pageNum)
        write(
            "<< /Type /Page /Parent ${pagesNum} 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] " +
            "/Resources << /Font << /F1 ${fontRegular} 0 R /F2 ${fontBold} 0 R >> >> " +
            "/Contents ${contentNum} 0 R >>\n"
        )
        writeObjEnd()

        def sb = new StringBuilder()
        sb << "BT\n"
        double cursorY = pageHeight - marginTop
        boolean first = true
        pageLines.each { entry ->
            String font = (entry.type == 'title' || entry.type == 'heading') ? 'F2' : 'F1'
            double size = entry.type == 'title' ? titleSize :
                          (entry.type == 'heading' ? headingSize :
                          (entry.type == 'small' ? smallSize : bodySize))
            double thisLineHeight = entry.type == 'title' ? titleSize * 1.4d :
                                     (entry.type == 'heading' ? headingSize * 1.4d : lineHeight)
            if (first) {
                sb << "/${font} ${size} Tf\n"
                sb << "${marginLeft} ${cursorY} Td\n"
                first = false
            } else {
                sb << "/${font} ${size} Tf\n"
                sb << "0 -${thisLineHeight} Td\n"
            }
            cursorY -= thisLineHeight
            sb << "(${escapePdfText(entry.text as String)}) Tj\n"
        }
        sb << "ET\n"

        String content = sb.toString()
        int contentLength = content.getBytes('ISO-8859-1').length
        writeObjStart(contentNum)
        write("<< /Length ${contentLength} >>\nstream\n${content}endstream\n")
        writeObjEnd()
    }

    int xrefStart = out.size()
    write("xref\n0 ${totalObjects + 1}\n")
    write("0000000000 65535 f \n")
    (1..totalObjects).each { num ->
        int off = (offsets[num] ?: 0) as int
        write(String.format('%010d 00000 n \n', off))
    }
    write("trailer\n<< /Size ${totalObjects + 1} /Root ${catalogNum} 0 R >>\nstartxref\n${xrefStart}\n%%EOF")

    return out.toByteArray()
}
