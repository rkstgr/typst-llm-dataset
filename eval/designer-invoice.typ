#set page(fill: luma(245), margin: (top: 6em, bottom: 4em, left:5em, right: 5em))
#set text(11pt, font: "DM Sans")
#let mono(content) = text(10pt, font: "DM Mono")[#content]

#let data = (
  freelancer: (
    name: "Erik Steiger",
    company_name: "SteigerLabs",
    street: "Leopoldstr. 10",
    zip_code: "81379 München",
    email: "erik@steigerlabs.com",
    website: "ersteiger.com"
  ),
  client: (
    name: "John Doe",
    company_name: "Corporate Client Inc.",
    street: "Maximiliansstr. 17",
    zip_code: "80801 München",
    number: "C-108"
  ),
  invoice: (
    invoice_number: "R-0291",
    date: "22.05.2025"
  ),
  services: (
    (name: "Exploration", description: "Research and discovery phase including user interviews, market analysis, and requirement gathering", amount: 1500.00),
    (name: "Design", description: "Complete visual design system including wireframes, mockups, prototypes, and brand guidelines", amount: 5200),
  ),
  banking: (
    (iban: "DE89 3704 0044 0532 0130 00", bic: " INGDDEFFXXX", taxnumber: "12/345/67890")
  ),
  postfix: ""
)

#let add_commas(n, width: none) = {
  let s = str(n)

  // Split on decimal point
  let parts = s.split(".")
  let integer_part = parts.at(0)
  let decimal_part = if parts.len() > 1 { parts.at(1) } else { "" }

  // Add thousand separators to integer part
  let result = ""
  let len = integer_part.len()
  for i in range(len) {
    if i > 0 and calc.rem(len - i, 3) == 0 {
      result += "."
    }
    result += integer_part.at(i)
  }

  // Add decimal part with comma separator (always 2 digits)
  if decimal_part != "" {
    // Pad or truncate decimal part to exactly 2 digits
    if decimal_part.len() == 1 {
      decimal_part += "0"
    } else if decimal_part.len() > 2 {
      decimal_part = decimal_part.slice(0, 2)
    }
    result += "," + decimal_part
  } else {
    // No decimal part, add ,00
    result += ",00"
  }

  // Pad with whitespace if width is specified
  if width != none {
    let current_len = result.len()
    if current_len < width {
      let padding = " " * (width - current_len)
      result = padding + result
    }
  }

  result
}

// Header with logo placeholder and freelancer info
#align(center)[
  #grid(
    columns: (1fr, 2fr, 1fr),
    column-gutter: 1em,
    align: (left, center, right),

    // Logo placeholder
    image("logo3.png", height: 60pt),

    [],
    // Freelancer info (right aligned)
    align(left)[
      #text(weight: "bold")[#data.freelancer.name] \
      #data.freelancer.company_name\

      #data.freelancer.street\
      #data.freelancer.zip_code
    ]
  )
]

#let divider = line(length: 100%, stroke: luma(200))

#v(2em)
#divider
#v(4em)

// Client address
#block[
  #data.client.name \
  #data.client.company_name\

  #data.client.street \
  #data.client.zip_code
]

#v(2em)

#let chip(title, value) = {
  stack(spacing: 1em,
  text(fill: luma(100))[#title],
  mono(value)
  )
}

// Invoice details grid
#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  column-gutter: 1em,
  row-gutter: 0.5em,
  chip([Invoice\#], data.invoice.invoice_number),
  chip([Client\#], data.client.number),
  chip([Date], data.invoice.date),
  [], []
)

#v(1.5em)

// Services table
#let service_table = table(
  columns: (3fr, 1fr),
  stroke: none,
  align: (left, left),
  row-gutter: 0pt,
  inset: (x: 0pt,y: 15pt),

  // Header
  table.header(text(luma(100))[Services], text(luma(100))[Amount]),

  // Separator line
  table.hline(stroke: luma(180)),

  // Services rows
  ..data.services.map(service => (
    [
      #grid(
        columns: (4fr, 1fr),
        stack(
        spacing: 7pt,
        [#text(weight: "bold")[#service.name]],
        [#text(size: 0.9em)[#service.description]]
      ),[]
      )

    ],
    mono[#add_commas(service.amount, width: 8) €]
  )).flatten()

)

#service_table

#v(1em)
#h(1fr)
#divider

// Totals section
#let subtotal = data.services.map(s => s.amount).sum()
#let vat_amount = subtotal * 0.19
#let total = subtotal * 1.19

#align(right)[
  #grid(
    columns: (2fr, 1fr, 1fr),
    row-gutter: 10pt,
    align: (left, left),
    [], [Subtotal], [#mono(add_commas(subtotal, width: 8)) €],
    [], [VAT (19%)], [#mono(add_commas(calc.round(vat_amount, digits: 2), width: 8)) €],
    [],[*Total*], text(weight: "bold", font: "DM Mono", 10pt)[
      #add_commas(calc.round(total, digits: 2), width: 8) €], []
  )
]

#v(1fr)

#text(8pt)[
#data.postfix
]

#v(1em)

#let pagefooter() = {
  set text(font: "DM Mono", 8pt)
  line(length: 100%, stroke: luma(100))
  grid(
    columns: (1fr, 2fr, 1fr),
    [
      #data.freelancer.name\
      \
      #data.freelancer.email\
      #data.freelancer.website
    ],
    [
      ING Diba\
      \
      #text(fill: luma(100))[IBAN]: #data.banking.iban\
      #text(fill: luma(100))[BIC]: #data.banking.bic
    ],
    [
      Munich\
      \
      Taxnumber\
      #data.banking.taxnumber
    ]
  )
}

#pagefooter()
