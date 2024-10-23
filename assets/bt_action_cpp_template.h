#ifndef PATHTOFILE_ACTIONCLASSNAME_H_
#define PATHTOFILE_ACTIONCLASSNAME_H_

#include <optional>
#include <cstdint>

#include "behaviortree_cpp/bt_factory.h"
#include "behaviortree_ros2/bt_action_node.hpp"
#include "action_package_name/action/action_name.hpp"
#include "rclcpp_action/rclcpp_action.hpp"

class ActionClassName
    : public BT::RosActionNode<
          action_package_name::action::ActionName> {
public:
  ActionClassName(const std::string& name, const BT::NodeConfig& conf,
                    const BT::RosNodeParams& params,
                    std::optional<unsigned> default_arg1 = std::nullopt,
                    std::optional<unsigned> default_arg2 = std::nullopt)
      : BT::RosActionNode<
            action_package_name::action::ActionName>(
            name, conf, params),
        default_arg1_(default_arg1),
        default_arg2_(default_arg2) {}

  static BT::PortsList providedPorts() {  // NOLINT
    return providedBasicPorts({BT::InputPort<unsigned>("default_arg1"),
                                BT::InputPort<unsigned>("default_arg2"),
                                BT::InputPort<unsigned>("arg3"),
                                BT::InputPort<unsigned>("arg4")});
  }

  bool setGoal(action_package_name::action::ActionName::Goal&
                  goal) override {
    unsigned default_arg1;
    unsigned default_arg2;
    unsigned arg3;
    unsigned arg4;

    if (default_arg1_.has_value()) {
      default_arg1 = default_arg1_.value();
    } else {
      getInput<unsigned>("default_arg1", default_arg1);
    }
    if (default_arg1_.has_value()) {
      default_arg2 = default_arg1_.value();
    } else {
      getInput<unsigned>("default_arg2", default_arg2);
    }

    goal.default_arg1 = default_arg1;
    goal.default_arg2 = default_arg2;
    goal.arg3 = arg3;
    goal.arg4 = arg4;
    return true;
  }

  BT::NodeStatus onResultReceived(const WrappedResult& result) override {
    if (result.code ==  rclcpp_action::ResultCode::SUCCEEDED) {
      return BT::NodeStatus::SUCCESS;
    } else {
      return BT::NodeStatus::FAILURE;
    }
  }

  BT::NodeStatus onFeedback(const std::shared_ptr<const Feedback> feedback) override {
    return BT::NodeStatus::RUNNING;
  }

  BT::NodeStatus onFailure(BT::ActionNodeErrorCode error_code) override {
    return BT::NodeStatus::FAILURE;
  }

private:
  std::optional<unsigned> default_arg1_;
  std::optional<unsigned> default_arg2_;
};

#endif  // PATHTOFILE_ACTIONCLASSNAME_H_