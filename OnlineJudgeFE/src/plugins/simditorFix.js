// Simditor 修复补丁
// 解决 Simditor.connect 不存在的问题

// 为Simditor添加缺失的方法
function patchSimditor(Simditor) {
  // 如果 connect 方法不存在，则添加一个空实现
  if (typeof Simditor.connect !== "function") {
    Simditor.connect = function () {
      console.warn("Simditor.connect is not implemented");
    };
  }

  // 确保 Simditor.prototype 存在
  if (!Simditor.prototype) {
    Simditor.prototype = {};
  }

  return Simditor;
}

export default patchSimditor;
