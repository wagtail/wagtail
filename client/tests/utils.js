expect.extend({
  toHaveSameBlockIdAs(received, otherChild) {
    const { id: thisId } = received;
    const { id: otherId } = otherChild;

    if (thisId === undefined || thisId === null) {
      return {
        message: 'expected block id not to be null or undefined',
        pass: false,
      };
    }

    if (otherId === undefined || otherId === null) {
      return {
        message: 'expected other block id not to be null or undefined',
        pass: false,
      };
    }

    return thisId === otherId
      ? {
          message: () =>
            `expected block id '${thisId}' not to match other id '${otherId}'`,
          pass: true,
        }
      : {
          message: () =>
            `expected block id '${thisId}' to match other id '${otherId}'`,
          pass: false,
        };
  },
});
