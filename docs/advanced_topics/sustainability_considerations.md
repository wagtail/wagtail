# Sustainability considerations

Here are guidelines and resources we recommend for projects with sustainability goals relating to climate action, such as the UN’s [Sustainable Development Goal 13: Climate action](https://sdgs.un.org/goals/goal13), and [SBTi’s Corporate Net-Zero Standard](https://sciencebasedtargets.org/net-zero).

## Standards

To account for the emissions of websites and track their reduction, we recommend the following:

-   ITU [L.1420](https://www.itu.int/rec/T-REC-L.1420) and [L.1430](https://www.itu.int/rec/T-REC-L.1430)
-   GHG Protocol [Product Life Cycle Accounting and Reporting Standard](https://ghgprotocol.org/product-standard) (Scope 3), and its additional [ICT Sector Guidance](https://ghgprotocol.org/guidance-built-ghg-protocol).

Those are the same standards used to assess the [sustainability of Wagtail](https://wagtail.org/sustainability/).

## Guidelines

Here are the guidelines we would recommend applying to Wagtail websites:

-   [Sustainable Web Design W3C Interest Group](https://www.w3.org/groups/ig/sustainableweb/) working draft of the [Web Sustainability Guidelines](https://w3c.github.io/sustainableweb-wsg/)
-   [Sustainable Web Design](https://sustainablewebdesign.org/)
-   [GR491](https://gr491.isit-europe.org/en/)
-   [Green Design Principles by Microsoft (PDF)](https://wxcteam.microsoft.com/download/Microsoft-Green-Design-Principles.pdf)
-   [Green Software Foundation Patterns](https://patterns.greensoftware.foundation/catalog/web/)

## Quantifying emissions

To quantify the emissions of a Wagtail website, we recommend three different approaches:

-   The [Sustainable Web Design](https://sustainablewebdesign.org/calculating-digital-emissions/) model, which uses page weight as a metric of energy efficiency, and page views as a metric of site utilization. This model has clear [known limitations](https://www.fershad.com/writing/is-data-the-best-proxy-for-website-carbon-emissions/), but is nonetheless ideal to provide high-level figures for a wide range of websites or pages.
-   Infrastructure-based calculators such as [Cloud Carbon Footprint](https://www.cloudcarbonfootprint.org/), a measurement and analysis tools.
-   Measurement orchestration tools such as [Green Metrics](https://github.com/green-coding-berlin/green-metrics-tool), [GreenFrame](https://greenframe.io/), [Scaphandre](https://github.com/hubblo-org/scaphandre).

---

We are working on those considerations as part of Wagtail's development process. An example of this is the two [Google Summer of Code internships focusing on sustainability](https://wagtail.org/blog/going-green-with-google-summer-of-code/), in partnership with the [Green Web Foundation and Green Coding Berlin](https://github.com/wagtail/wagtail/discussions/8843).
