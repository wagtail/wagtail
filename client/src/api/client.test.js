import client from './client';

describe('client API', () => {
  it('should succeed fetching', (done) => {
    const response = '{"meta":{"total_count":1},"items":[]}';
    fetch.mockResponseSuccess(response);

    client.get('/example/url').then((result) => {
      expect(result).toMatchSnapshot();
      done();
    });
  });

  it('should fail fetching', (done) => {
    fetch.mockResponseFailure();

    client.get('/example/url').catch((result) => {
      expect(result).toMatchSnapshot();
      done();
    });
  });

  it('should crash fetching', (done) => {
    fetch.mockResponseCrash();

    client.get('/example/url').catch((result) => {
      expect(result).toMatchSnapshot();
      done();
    });
  });

  it('should timeout fetching', (done) => {
    jest.useFakeTimers();
    fetch.mockResponseTimeout();

    client.get('/example/url').catch((result) => {
      expect(result).toMatchSnapshot();
      done();
    });

    jest.runOnlyPendingTimers();
  });
});
