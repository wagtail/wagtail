import Enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';

Enzyme.configure({
  adapter: new Adapter(),
});

/** Mock window.scrollTo as not provided via JSDom */
window.scrollTo = jest.fn();

/** Mock scrollIntoView on elements, this is not provided by JSDom */
Element.prototype.scrollIntoView = jest.fn();
