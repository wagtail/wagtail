import { Application } from '@hotwired/stimulus'
import AutosizeController from "./AutoSizeController"

const application = Application.start()
application.register("autosize", AutosizeController)

describe("AutosizeController", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <textarea class="js-autosize"></textarea>
    `
  })

  it("expands the textarea on input", () => {
    const textarea = document.querySelector(".js-autosize")
    textarea.value = "Short text"
    textarea.dispatchEvent(new Event("input"))

    expect(textarea.style.height).toBe("auto")
    expect(textarea.clientHeight).toBeGreaterThan(20)
  })

  it("shrinks the textarea on clearing the value", () => {
    const textarea = document.querySelector(".js-autosize")
    textarea.value = "Long text".repeat(10)
    textarea.dispatchEvent(new Event("input"))

    expect(textarea.style.height).toBe("auto")
    expect(textarea.clientHeight).toBeGreaterThan(200)

    textarea.value = ""
    textarea.dispatchEvent(new Event("input"))

    expect(textarea.style.height).toBe("auto")
    expect(textarea.clientHeight).toBeLessThan(100)
  })

  it("destroys the autosize instance on disconnect", () => {
    const textarea = document.querySelector(".js-autosize")
    const controller = application.getControllerForElementAndIdentifier(textarea, "autosize")

    // eslint-disable-next-line no-undef
    spyOn(controller.autosize, "destroy")
    controller.disconnect()

    expect(controller.autosize.destroy).toHaveBeenCalled()
  })
})