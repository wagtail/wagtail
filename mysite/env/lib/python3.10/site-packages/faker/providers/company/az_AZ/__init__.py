from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        "{{last_name}} {{company_suffix}}",
        "{{last_name}} {{last_name}} {{company_suffix}}",
        "{{large_company}}",
    )

    large_companies = (
        "AZAL",
        "Azergold",
        "SOCAR",
        "Socar Polymer",
        "Global Export Fruits",
        "Baku Steel Company",
        "Azersun",
        "Sun Food",
        "Azərbaycan Şəkər İstehsalat Birliyi",
        "Azərsu",
        "Xəzər Dəniz Gəmiçiliyi",
        "Azərenerji",
        "Bakıelektrikşəbəkə",
        "Azəralüminium",
        "Bravo",
        "Azərpambıq Aqrar Sənaye Kompleksi",
        "CTS-Agro",
        "Azərtütün Aqrar Sənaye Kompleksi",
        "Azəripək",
        "Azfruittrade",
        "AF Holding",
        "Azinko Holding",
        "Gilan Holding",
        "Azpetrol",
        "Azərtexnolayn",
        "Bakı Gəmiqayırma Zavodu",
        "Gəncə Tekstil Fabriki",
        "Mətanət A",
        "İrşad Electronics",
    )
    company_suffixes = (
        "ASC",
        "QSC",
        "MMC",
    )

    def large_company(self):
        """
        :example: 'SOCAR'
        """
        return self.random_element(self.large_companies)
