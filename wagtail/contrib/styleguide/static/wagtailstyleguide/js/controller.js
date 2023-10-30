const { Controller } = window.StimulusModule;

class ExampleController extends Controller {
  static targets = ['bar'];
  static values = { delay: Array, max: Number, min: Number };

  connect() {
    this.runProgress();
  }

  runProgress() {
    const minValue = `${this.minValue}%`;
    const maxValue = `${this.maxValue}%`;
    const [lowDelay, highDelay] = this.delayValue;

    const timer = setTimeout(() => {
      this.runProgress();
      clearTimeout(timer);
      setTimeout(() => {
        this.barTarget.style.width = minValue;
        this.barTarget.innerText = minValue;
      }, lowDelay);
    }, highDelay);
    this.barTarget.style.width = maxValue;
    this.barTarget.innerText = maxValue;
  }
}

window.wagtail.app.register('x', ExampleController);
