import React from 'react';
import { shallow } from 'enzyme';
import PageChooserResult from './PageChooserResult';

describe('PageChooserResult', () => {
  it('renders', () => {
    expect(shallow((
      <PageChooserResult
        isChoosable={false}
        onChoose={() => {}}
        onNavigate={() => {}}
        page={{
          meta: {
            status: {},
          },
        }}
      />
    ))).toMatchSnapshot();
  });
});
